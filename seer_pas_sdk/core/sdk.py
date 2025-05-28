from tqdm import tqdm

import os
import jwt
import requests
import urllib.request
import ssl

from typing import List as _List, Tuple as _Tuple

from ..common import *
from ..auth import Auth
from ..objects.volcanoplot import VolcanoPlotBuilder


class SeerSDK:
    """
    Object exposing SDK methods. Requires a username and password; the optional `instance` param denotes the instance of PAS (defaults to "US").

    Examples
    -------
    >>> from seer_pas_sdk import SeerSDK
    >>> USERNAME = "test"
    >>> PASSWORD = "test-password"
    >>> INSTANCE = "EU"
    >>> seer_sdk = SeerSDK(USERNAME, PASSWORD, INSTANCE)
    """

    def __init__(self, username, password, instance="US", tenant=None):
        try:
            self._auth = Auth(username, password, instance)

            self._auth.get_token()
            print(f"User '{username}' logged in.\n")

            if not tenant:
                tenant = self._auth.active_tenant_id
            try:
                self.switch_tenant(tenant)
            except Exception as e:
                print(
                    f"Encountered an error directing you to tenant {tenant}: {e}."
                )
                print("Logging into home tenant...")
                # If an error occurs while directing the user to a tenant, default to home tenant.
                print(f"You are now active in {self.get_active_tenant_name()}")
        except Exception as e:
            raise ValueError(
                f"Could not log in.\nPlease check your credentials and/or instance: {e}."
            )

    def _get_auth_headers(self, use_multi_tenant=True):
        id_token, access_token = self._auth.get_token()
        header = {
            "Authorization": id_token,
            "Access-Token": access_token,
        }
        if use_multi_tenant:
            multi_tenant = {
                "Tenant-Id": self._auth.active_tenant_id,
                "Role": self._auth.active_role,
            }
            header.update(multi_tenant)
        return header

    def _get_auth_session(self, use_multi_tenant=True):
        sess = requests.Session()

        sess.headers.update(self._get_auth_headers(use_multi_tenant))

        return sess

    def get_user_tenant_metadata(self, index=True):
        """
        Fetches the tenant metadata for the authenticated user.

        Returns
        -------
        response : dict
            A dictionary containing the tenant metadata for the authenticated user.
        """
        with self._get_auth_session() as s:
            response = s.get(f"{self._auth.url}api/v1/usertenants")

            if response.status_code != 200:
                raise ValueError(
                    "Invalid request. Please check your parameters."
                )

            response = response.json()
            if index:
                return {x["institution"]: x for x in response}
            else:
                return response

    def list_tenants(self, reverse=False):
        """
        Lists the institution names and the tenant ids for the authenticated user.

        Parameters
        ----------
        reverse: bool
            Boolean denoting whether the user wants the result dictionary indexed by tenant id (True) or institution name (False).

        Returns
        -------
        tenants : dict
            A dictionary containing the institution names and tenant ids for the authenticated user.
        """
        tenants = self.get_user_tenant_metadata()
        if reverse:
            return {x["tenantId"]: x["institution"] for x in tenants.values()}
        else:
            return {x["institution"]: x["tenantId"] for x in tenants.values()}

    def switch_tenant(self, identifier: str):
        """
        Switches the tenant for the authenticated user.

        Parameters
        ----------
        identifier: str
            Tenant ID or organization name to switch to.

        Returns
        -------
        tenant_id: str
            Returns the value of the active tenant id after the operation.
        """
        map = self.get_user_tenant_metadata()
        tenant_ids = [x["tenantId"] for x in map.values()]
        institution_names = map.keys()

        if identifier in tenant_ids:
            tenant_id = identifier
            row = [x for x in map.values() if x["tenantId"] == tenant_id]
            if row:
                row = row[0]
            else:
                raise ValueError(
                    "Invalid tenant identifier. Tenant was not switched."
                )
        elif identifier in institution_names:
            row = map[identifier]
            tenant_id = row["tenantId"]
        else:
            raise ValueError(
                "Invalid tenant identifier. Tenant was not switched."
            )

        with self._get_auth_session() as s:
            response = s.put(
                self._auth.url + "api/v1/users/tenant",
                json={
                    "currentTenantId": tenant_id,
                    "username": self._auth.username,
                },
            )
            if response.status_code != 200:
                raise ServerError(
                    "Could not update current tenant for user. Tenant was not switched."
                )

        self._auth.active_tenant_id = tenant_id
        self._auth.active_role = row["role"]
        print(f"You are now active in {row['institution']}")
        return self._auth.active_tenant_id, self._auth.active_role

    def get_active_tenant(self):
        """
        Fetches the active tenant for the authenticated user.

        Returns
        -------
        tenant: dict
            Tenant metadata for the authenticated user containing "institution" and "tenantId" keys.
        """
        tenants = self.get_user_tenant_metadata(index=False)
        row = [
            x for x in tenants if x["tenantId"] == self._auth.active_tenant_id
        ]
        return row[0] if row else None

    def get_active_tenant_id(self):
        """
        Fetches the active tenant ID for the authenticated user.

        Returns
        -------
        tenant_id: str
            Tenant ID for the authenticated user.
        """
        tenant = self.get_active_tenant()
        return tenant["tenantId"] if tenant else None

    def get_active_tenant_name(self):
        """
        Fetches the active tenant name for the authenticated user.

        Returns
        -------
        tenant: str
            Tenant name for the authenticated user.
        """
        tenant = self.get_active_tenant()
        return tenant["institution"] if tenant else None

    def get_spaces(self):
        """
        Fetches a list of spaces for the authenticated user.

        Returns
        -------
        spaces: list
            List of space objects for the authenticated user.

        Examples
        -------
        >>> from seer_pas_sdk import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.get_spaces()
        >>> [
                { "usergroup_name": ... },
                { "usergroup_name": ... },
                ...
            ]
        """

        URL = f"{self._auth.url}api/v1/usergroups"

        with self._get_auth_session() as s:
            spaces = s.get(URL)

            if spaces.status_code != 200:
                raise ValueError(
                    "Invalid request. Please check your parameters."
                )
            return spaces.json()

    def get_plate_metadata(self, plate_id: str = None, df: bool = False):
        """
        Fetches a list of plates for the authenticated user. If no `plate_id` is provided, returns all plates for the authenticated user. If `plate_id` is provided, returns the plate with the given `plate_id`, provided it exists.

        Parameters
        ----------
        plate_id : str, optional
            ID of the plate to be fetched, defaulted to None.
        df: bool
            Boolean denoting whether the user wants the response back in JSON or a DataFrame object

        Returns
        -------
        plates: list or DataFrame
            List/DataFrame of plate objects for the authenticated user.

        Examples
        -------
        >>> from seer_pas_sdk import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.get_plate_metadata()
        >>> [
                { "id": ... },
                { "id": ... },
                ...
            ]
        >>> seer_sdk.get_plate_metadata(df=True)
        >>>                                        id  ... user_group
            0    a7c12190-15da-11ee-bdf1-bbaa73585acf  ...       None
            1    8c3b1480-15da-11ee-bdf1-bbaa73585acf  ...       None
            2    6f158840-15da-11ee-bdf1-bbaa73585acf  ...       None
            3    1a8a2920-15da-11ee-bdf1-bbaa73585acf  ...       None
            4    7ab47f40-15d9-11ee-bdf1-bbaa73585acf  ...       None
            ..                                    ...  ...        ...
            935  8fa91c00-6621-11ea-96e3-d5a4dab4ebf6  ...       None
            936  53180b20-6621-11ea-96e3-d5a4dab4ebf6  ...       None
            937  5c31fe90-6618-11ea-96e3-d5a4dab4ebf6  ...       None
            938  5b05d440-6610-11ea-96e3-d5a4dab4ebf6  ...       None
            939  9872e3f0-544e-11ea-ad9e-1991e0725494  ...       None

        >>> seer_sdk.get_plate_metadata(id="YOUR_PLATE_ID_HERE")
        >>> [{ "id": ... }]
        """

        URL = f"{self._auth.url}api/v1/plates"
        res = []

        with self._get_auth_session() as s:

            plates = s.get(
                f"{URL}/{plate_id}" if plate_id else URL,
                params={"all": "true"},
            )
            if plates.status_code != 200:
                raise ValueError(
                    "Invalid request. Please check your parameters."
                )
            if not plate_id:
                res = plates.json()["data"]
            else:
                res = [plates.json()]

            for entry in res:
                del entry["tenant_id"]

        return res if not df else dict_to_df(res)

    def get_project_metadata(self, project_id: str = None, df: bool = False):
        """
        Fetches a list of projects for the authenticated user. If no `project_id` is provided, returns all projects for the authenticated user. If `project_id` is provided, returns the project with the given `project_id`, provided it exists.

        Parameters
        ----------
        project_id: str, optional
            Project ID of the project to be fetched, defaulted to None.
        df: bool
            Boolean denoting whether the user wants the response back in JSON or a DataFrame object.

        Returns
        -------
        projects: list or DataFrame
            DataFrame or list of project objects for the authenticated user.

        Examples
        -------
        >>> from seer_pas_sdk import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.get_project_metadata()
        >>> [
                { "project_name": ... },
                { "project_name": ... },
                ...
            ]

        >>> seer_sdk.get_project_metadata(df=True)
        >>>                                        id  ... user_group
            0    a7c12190-15da-11ee-bdf1-bbaa73585acf  ...       None
            1    8c3b1480-15da-11ee-bdf1-bbaa73585acf  ...       None
            2    6f158840-15da-11ee-bdf1-bbaa73585acf  ...       None
            3    1a8a2920-15da-11ee-bdf1-bbaa73585acf  ...       None
            4    7ab47f40-15d9-11ee-bdf1-bbaa73585acf  ...       None
            ..                                    ...  ...        ...
            935  8fa91c00-6621-11ea-96e3-d5a4dab4ebf6  ...       None
            936  53180b20-6621-11ea-96e3-d5a4dab4ebf6  ...       None
            937  5c31fe90-6618-11ea-96e3-d5a4dab4ebf6  ...       None
            938  5b05d440-6610-11ea-96e3-d5a4dab4ebf6  ...       None
            939  9872e3f0-544e-11ea-ad9e-1991e0725494  ...       None

        >>> seer_sdk.get_project_metadata(id="YOUR_PROJECT_ID_HERE")
        >>> [{ "project_name": ... }]
        """

        URL = (
            f"{self._auth.url}api/v1/projects"
            if not project_id
            else f"{self._auth.url}api/v1/projects/{project_id}"
        )
        res = []

        with self._get_auth_session() as s:

            projects = s.get(URL, params={"all": "true"})
            if projects.status_code != 200:
                raise ValueError(
                    "Invalid request. Please check your parameters."
                )
            if not project_id:
                res = projects.json()["data"]
            else:
                res = [projects.json()]

        for entry in res:
            if "tenant_id" in entry:
                del entry["tenant_id"]

            if "raw_file_path" in entry:
                # Simple lambda function to find the third occurrence of '/' in the raw file path
                location = lambda s: len(s) - len(s.split("/", 3)[-1])
                # Slicing the string from the location
                entry["raw_file_path"] = entry["raw_file_path"][
                    location(entry["raw_file_path"]) :
                ]
        return res if not df else dict_to_df(res)

    def get_samples_metadata(
        self, plate_id: str = None, project_id: str = None, df: bool = False
    ):
        """
        Fetches a list of samples for the authenticated user, filtered by `plate_id`. Returns all samples for the plate with the given `plate_id`, provided it exists.

        If both `plate_id` and `project_id` are passed in, only the `plate_id` is validated first.

        Parameters
        ----------
        plate_id : str, optional
            ID of the plate for which samples are to be fetched, defaulted to None.
        project_id : str, optional
            ID of the project for which samples are to be fetched, defaulted to None.
        df: bool
            Boolean denoting whether the user wants the response back in JSON or a DataFrame object

        Returns
        -------
        samples: list or DataFrame
            List/DataFrame of samples for the authenticated user.

        Examples
        -------
        >>> from seer_pas_sdk import SeerSDK
        >>> seer_sdk = SeerSDK()

        >>> seer_sdk.get_samples_metadata(plate_id="7ec8cad0-15e0-11ee-bdf1-bbaa73585acf")
        >>> [
                { "id": ... },
                { "id": ... },
                ...
            ]

        >>> seer_sdk.get_samples_metadata(df=True)
        >>>                                     id  ...      control
        0     812139c0-15e0-11ee-bdf1-bbaa73585acf  ...
        1     803e05b0-15e0-11ee-bdf1-bbaa73585acf  ...  MPE Control
        2     a9b26a40-15da-11ee-bdf1-bbaa73585acf  ...
        3     a8fc87c0-15da-11ee-bdf1-bbaa73585acf  ...  MPE Control
        4     8e322990-15da-11ee-bdf1-bbaa73585acf  ...
        ...                                    ...  ...          ...
        3624  907e1f40-6621-11ea-96e3-d5a4dab4ebf6  ...         C132
        3625  53e59450-6621-11ea-96e3-d5a4dab4ebf6  ...         C132
        3626  5d11b030-6618-11ea-96e3-d5a4dab4ebf6  ...         C132
        3627  5bdf9270-6610-11ea-96e3-d5a4dab4ebf6  ...         C132
        3628  dd607ef0-654c-11ea-8eb2-25a1cfd1163c  ...         C132
        """

        if not plate_id and not project_id:
            raise ValueError("You must pass in plate ID or project ID.")

        res = []
        URL = f"{self._auth.url}api/v1/samples"
        sample_params = {"all": "true"}

        with self._get_auth_session() as s:

            if plate_id:
                try:
                    self.get_plate_metadata(plate_id)
                except:
                    raise ValueError("Plate ID is invalid.")
                sample_params["plateId"] = plate_id

            elif project_id:
                try:
                    self.get_project_metadata(project_id)
                except:
                    raise ValueError("Project ID is invalid.")

                sample_params["projectId"] = project_id

            samples = s.get(URL, params=sample_params)
            if samples.status_code != 200:
                raise ValueError(
                    f"Failed to fetch sample data for plate ID: {plate_id}."
                )
            res = samples.json()["data"]

            for entry in res:
                del entry["tenant_id"]

        # Exclude custom fields that don't belong to the tenant
        res_df = dict_to_df(res)
        custom_columns = [
            x["field_name"] for x in self.get_sample_custom_fields()
        ]
        res_df = res_df[
            [
                x
                for x in res_df.columns
                if not x.startswith("custom_") or x in custom_columns
            ]
        ]

        # API returns empty strings if not a control, replace with None for filtering purposes
        res_df["control"] = res_df["control"].apply(lambda x: x if x else None)

        return res_df.to_dict(orient="records") if not df else res_df

    def _filter_samples_metadata(
        self,
        project_id: str,
        filter: str,
        sample_ids: list = None,
    ):
        """
        ****************
        [UNEXPOSED METHOD CALL]
        ****************
        Get samples given a filter and project_id.

        Parameters
        ----------
        project_id : str
            The project id.
        filter : str
            The filter to be applied. Acceptable values are 'control' or 'sample'.
        sample_ids : list, optional
            List of user provided sample ids

        Returns
        -------
        res : list
            A list of sample ids

        Examples
        -------
        >>> from core import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk._get_samples_filter("FILTER", "PROJECT_ID")
        >>> {
                "samples": [
                    {
                        "id": "SAMPLE_ID",
                        "plate_id": "PLATE_ID",
                        "sample_name": "SAMPLE_NAME",
                        ...
                        ...
                    },
                    ...
                    ...
                ]
            }
        """

        if filter and filter not in ["control", "sample"]:
            raise ValueError(
                "Invalid filter. Please choose between 'control' or 'sample'."
            )

        df = self.get_samples_metadata(project_id=project_id, df=True)

        if filter == "control":
            df = df[~df["control"].isna()]
        elif filter == "sample":
            df = df[df["control"].isna()]

        valid_samples = df["id"].tolist()
        if sample_ids:
            valid_samples = list(set(valid_samples) & set(sample_ids))

        return valid_samples

    def get_sample_custom_fields(self):
        """
        Fetches a list of custom fields defined for the authenticated user.
        """
        URL = f"{self._auth.url}api/v1/samplefields"

        with self._get_auth_session() as s:

            fields = s.get(URL)

            if fields.status_code != 200:
                raise ValueError(
                    "Failed to fetch custom columns. Please check your connection."
                )

            res = fields.json()
            for entry in res:
                del entry["tenant_id"]
            return res

    def get_msdata(self, sample_ids: list, df: bool = False):
        """
        Fetches MS data files for passed in `sample_ids` (provided they are valid and contain relevant files) for an authenticated user.

        The function returns a dict containing DataFrame objects if the `df` flag is passed in as True, otherwise a nested dict object is returned instead.

        Parameters
        ----------
        sample_ids : list
            List of unique sample IDs.
        df: bool
            Boolean denoting whether the user wants the response back in JSON or a DataFrame object.

        Returns
        -------
        res: list or DataFrame
            List/DataFrame of plate objects for the authenticated user.

        Examples
        -------
        >>> from seer_pas_sdk import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> sample_ids = ["812139c0-15e0-11ee-bdf1-bbaa73585acf", "803e05b0-15e0-11ee-bdf1-bbaa73585acf"]

        >>> seer_sdk.get_msdata(sample_ids)
        >>> [
            {"id": "SAMPLE_ID_1_HERE" ... },
            {"id": "SAMPLE_ID_2_HERE" ... }
        ]

        >>> seer_sdk.get_msdata(sample_ids, df=True)
        >>>                                      id  ... gradient
            0  81c6a180-15e0-11ee-bdf1-bbaa73585acf  ...     None
            1  816a9ed0-15e0-11ee-bdf1-bbaa73585acf  ...     None

            [2 rows x 26 columns]
        """

        URL = f"{self._auth.url}api/v1/msdatas/items"

        res = []
        for sample_id in sample_ids:

            with self._get_auth_session() as s:

                msdatas = s.post(URL, json={"sampleId": sample_id})

                if msdatas.status_code != 200 or not msdatas.json()["data"]:
                    raise ValueError(
                        f"Failed to fetch MS data for sample ID={sample_id}."
                    )

                res += [x for x in msdatas.json()["data"]]

        for entry in res:
            if "tenant_id" in entry:
                del entry["tenant_id"]

            if "raw_file_path" in entry:
                # Simple lambda function to find the third occurrence of '/' in the raw file path
                location = lambda s: len(s) - len(s.split("/", 3)[-1])
                # Slicing the string from the location
                entry["raw_file_path"] = entry["raw_file_path"][
                    location(entry["raw_file_path"]) :
                ]
        return res if not df else dict_to_df(res)

    def get_plate(self, plate_id: str, df: bool = False):
        """
        Fetches MS data files for a `plate_id` (provided that the `plate_id` is valid and has samples associated with it) for an authenticated user.

        The function returns a dict containing DataFrame objects if the `df` flag is passed in as True, otherwise a nested dict object is returned instead.

        Parameters
        ----------
        plate_id : str, optional
            ID of the plate for which samples are to be fetched, defaulted to None.
        df: bool
            Boolean denoting whether the user wants the response back in JSON or a DataFrame object

        Returns
        -------
        res: list or DataFrame
            List/DataFrame of MS data file objects for the authenticated user.

        Examples
        -------
        >>> from seer_pas_sdk import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> plate_id = "7ec8cad0-15e0-11ee-bdf1-bbaa73585acf"

        >>> seer_sdk.get_plate(plate_id)
        >>> [
            {"id": "PLATE_ID_1_HERE" ... },
            {"id": "PLATE_ID_2_HERE" ... }
        ]

        >>> seer_sdk.get_plate(plate_id, df=True)
        >>>                 id  ...   volume
            0  PLATE_ID_1_HERE  ...     None
            1  PLATE_ID_2_HERE  ...     None

            [2 rows x 26 columns]
        """
        plate_samples = self.get_samples_metadata(plate_id=plate_id)
        sample_ids = [sample["id"] for sample in plate_samples]
        return self.get_msdata(sample_ids, df)

    def get_project(
        self,
        project_id: str,
        msdata: bool = False,
        df: bool = False,
        flat: bool = False,
    ):
        """
        Fetches samples (and MS data files) for a `project_id` (provided that the `project_id` is valid and has samples associated with it) for an authenticated user.

        The function returns a DataFrame object if the `df` flag is passed in as True, otherwise a nested dict object is returned instead. If the both the `df` and `msdata` flags are passed in as True, then a nested DataFrame object is returned instead.

        If the `flat` flag is passed in as True, then the nested dict object is returned as an array of dict objects and the nested df object is returned as a single df object.

        Parameters
        ----------
        project_id : str
            ID of the project for which samples are to be fetched.
        msdata: bool, optional
            Boolean flag denoting whether the user wants relevant MS data files associated with the samples.
        df: bool, optional
            Boolean denoting whether the user wants the response back in JSON or a DataFrame object.

        Returns
        -------
        res: list or DataFrame
            List/DataFrame of plate objects for the authenticated user.

        Examples
        -------
        >>> from seer_pas_sdk import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> project_id = "7e48e150-8a47-11ed-b382-bf440acece26"

        >>> seer_sdk.get_project(project_id=project_id, msdata=False, df=False)
        >>> {
            "project_samples": [
                {
                    "id": "SAMPLE_ID_1_HERE",
                    "sample_type": "Plasma",
                    ...
                    ...
                },
                {
                    "id": "SAMPLE_ID_2_HERE",
                    "sample_type": "Plasma",
                    ...
                    ...
                }
            ]
        }

        >>> seer_sdk.get_project(project_id=project_id, msdata=True, df=False)
        >>> [
                {
                    "id": "SAMPLE_ID_1_HERE",
                    "sample_type": "Plasma",
                    ...
                    ...
                    "ms_data_files": [
                        {
                            "id": MS_DATA_FILE_ID_1_HERE,
                            "tenant_id": "TENANT_ID_HERE",
                            ...
                            ...
                        },
                        {
                            "id": MS_DATA_FILE_ID_1_HERE,
                            "tenant_id": "TENANT_ID_HERE",
                            ...
                            ...
                        }
                    ]
                },
                {
                    "id": "SAMPLE_ID_2_HERE",
                    "sample_type": "Plasma",
                    ...
                    ...
                    "ms_data_files": [
                        {
                            "id": MS_DATA_FILE_ID_2_HERE,
                            "tenant_id": "TENANT_ID_HERE",
                            ...
                            ...
                        },
                        {
                            "id": MS_DATA_FILE_ID_2_HERE,
                            "tenant_id": "TENANT_ID_HERE",
                            ...
                            ...
                        }
                    ]
                }
            ]

        >>> seer_sdk.get_project(project_id=project_id, msdata=True, df=True)
        >>> id  ...                                                                           ms_data_files
            0  829509f0-8a47-11ed-b382-bf440acece26  ...                                       id  ... g...
            1  828d41c0-8a47-11ed-b382-bf440acece26  ...                                       id  ... g...
            2  8294e2e0-8a47-11ed-b382-bf440acece26  ...                                       id  ... g...
            3  8285eec0-8a47-11ed-b382-bf440acece26  ...                                       id  ... g...

            [4 rows x 60 columns]
        """
        if not project_id:
            return ValueError("No project ID specified.")

        sample_ids = []
        project_samples = self.get_samples_metadata(
            project_id=project_id, df=False
        )
        flat_result = []

        if msdata:

            # construct map for quick index reference of sample in project_samples
            sample_ids = {
                sample["id"]: i for i, sample in enumerate(project_samples)
            }  # will always contain unique values
            ms_data_files = self.get_msdata(
                sample_ids=list(sample_ids.keys()), df=False
            )

            for ms_data_file in ms_data_files:
                index = sample_ids.get(ms_data_file["sample_id"], None)
                if not index:
                    continue

                if not flat:
                    if "ms_data_file" not in project_samples[index]:
                        project_samples[index]["ms_data_files"] = [
                            ms_data_file
                        ]
                    else:
                        project_samples[index]["ms_data_files"].append(
                            ms_data_file
                        )
                else:
                    flat_result.append(project_samples[index] | ms_data_file)

        # return flat result if results were added to the flat object
        if flat and flat_result:
            project_samples = flat_result

        if df:
            if flat:
                return pd.DataFrame(project_samples)
            else:
                for sample_index in range(len(project_samples)):
                    if "ms_data_files" in project_samples[sample_index]:
                        project_samples[sample_index]["ms_data_files"] = (
                            dict_to_df(
                                project_samples[sample_index]["ms_data_files"]
                            )
                        )

            project_samples = dict_to_df(project_samples)

        return project_samples

    def get_analysis_protocols(
        self,
        analysis_protocol_name: str = None,
        analysis_protocol_id: str = None,
    ):
        """
        Fetches a list of analysis protocols for the authenticated user. If no `analysis_protocol_id` is provided, returns all analysis protocols for the authenticated user. If `analysis_protocol_name` (and no `analysis_protocol_id`) is provided, returns the analysis protocol with the given name, provided it exists.

        Parameters
        ----------
        analysis_protocol_id : str, optional
            ID of the analysis protocol to be fetched, defaulted to None.

        analysis_protocol_name : str, optional
            Name of the analysis protocol to be fetched, defaulted to None.

        Returns
        -------
        protocols: list
            List of analysis protocol objects for the authenticated user.

        Examples
        -------
        >>> from seer_pas_sdk import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.get_analysis_protocols()
        >>> [
                { "id": ..., "analysis_protocol_name": ... },
                { "id": ..., "analysis_protocol_name": ... },
                ...
            ]

        >>> seer_sdk.get_analysis_protocols(name="YOUR_ANALYSIS_PROTOCOL_NAME_HERE")
        >>> [{ "id": ..., "analysis_protocol_name": ... }]

        >>> seer_sdk.get_analysis_protocols(id="YOUR_ANALYSIS_PROTOCOL_ID_HERE")
        >>> [{ "id": ..., "analysis_protocol_name": ... }]

        >>> seer_sdk.get_analysis_protocols(id="YOUR_ANALYSIS_PROTOCOL_ID_HERE", name="YOUR_ANALYSIS_PROTOCOL_NAME_HERE")

        >>> [{ "id": ..., "analysis_protocol_name": ... }] # in this case the id would supersede the inputted name.
        """

        URL = (
            f"{self._auth.url}api/v1/analysisProtocols"
            if not analysis_protocol_id
            else f"{self._auth.url}api/v1/analysisProtocols/{analysis_protocol_id}"
        )
        res = []

        with self._get_auth_session() as s:

            protocols = s.get(URL, params={"all": "true"})
            if protocols.status_code != 200:
                raise ValueError(
                    "Invalid request. Please check your parameters."
                )
            if not analysis_protocol_id and not analysis_protocol_name:
                res = protocols.json()["data"]

            if analysis_protocol_id and not analysis_protocol_name:
                res = [protocols.json()]

            if not analysis_protocol_id and analysis_protocol_name:
                res = [
                    protocol
                    for protocol in protocols.json()["data"]
                    if protocol["analysis_protocol_name"]
                    == analysis_protocol_name
                ]

            for entry in range(len(res)):
                if "tenant_id" in res[entry]:
                    del res[entry]["tenant_id"]

                if "parameter_file_path" in res[entry]:
                    # Simple lambda function to find the third occurrence of '/' in the raw file path
                    location = lambda s: len(s) - len(s.split("/", 3)[-1])
                    # Slicing the string from the location
                    res[entry]["parameter_file_path"] = res[entry][
                        "parameter_file_path"
                    ][location(res[entry]["parameter_file_path"]) :]

            return res

    def get_analysis(
        self,
        analysis_id: str = None,
        folder_id: str = None,
        show_folders: bool = True,
        analysis_only: bool = True,
        project_id: str = None,
        plate_name: str = None,
        **kwargs,
    ):
        """
        Returns a list of analyses objects for the authenticated user. If no id is provided, returns all analyses for the authenticated user.
        Search parameters may be passed in as keyword arguments to filter the results. Acceptable values are 'analysis_name', 'folder_name', 'description', 'notes', or 'number_msdatafile'.
        Only search on a single field is supported.

        Parameters
        ----------
        analysis_id : str, optional
            ID of the analysis to be fetched, defaulted to None.

        folder_id : str, optional
            ID of the folder to be fetched, defaulted to None.

        show_folders : bool, optional
            Mark True if folder contents are to be returned in the response, i.e. recursive search, defaulted to True.
            Will be disabled if an analysis id is provided.

        analysis_only : bool, optional
            Mark True if only analyses objects are to be returned in the response, defaulted to True.
            If marked false, folder objects will also be included in the response.

        project_id : str, optional
            ID of the project to be fetched, defaulted to None.

        plate_name : str, optional
            Name of the plate to be fetched, defaulted to None.

        **kwargs : dict, optional
            Search keyword parameters to be passed in. Acceptable values are 'analysis_name', 'folder_name', 'analysis_protocol_name', 'description', 'notes', or 'number_msdatafile'.

        Returns
        -------
        analyses: dict
            Contains a list of analyses objects for the authenticated user.

        Examples
        -------
        >>> from seer_pas_sdk import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.get_analysis()
        >>> [
                {id: "YOUR_ANALYSIS_ID_HERE", ...},
                {id: "YOUR_ANALYSIS_ID_HERE", ...},
                {id: "YOUR_ANALYSIS_ID_HERE", ...}
            ]

        >>> seer_sdk.get_analysis("YOUR_ANALYSIS_ID_HERE")
        >>> [{ id: "YOUR_ANALYSIS_ID_HERE", ...}]

        >>> seer_sdk.get_analysis(folder_name="YOUR_FOLDER_NAME_HERE")
        >>> [{ id: "YOUR_ANALYSIS_ID_HERE", ...}]

        >>> seer_sdk.get_analysis(analysis_name="YOUR_ANALYSIS")
        >>> [{ id: "YOUR_ANALYSIS_ID_HERE", ...}]

        >>> seer_sdk.get_analysis(description="YOUR_DESCRIPTION")
        >>> [{ id: "YOUR_ANALYSIS_ID_HERE", ...}]
        """

        URL = f"{self._auth.url}api/v1/analyses"
        res = []

        search_field = None
        search_item = None
        if kwargs:
            if len(kwargs.keys()) > 1:
                raise ValueError("Please include only one search parameter.")
            search_field = list(kwargs.keys())[0]
            search_item = kwargs[search_field]

            if not search_item:
                raise ValueError(
                    f"Please provide a non null value for {search_field}"
                )

        if search_field and search_field not in [
            "analysis_name",
            "folder_name",
            "analysis_protocol_name",
            "description",
            "notes",
            "number_msdatafile",
        ]:
            raise ValueError(
                "Invalid search field. Please choose between 'analysis_name', 'folder_name', 'analysis_protocol_name', 'description', 'notes', or 'number_msdatafile'."
            )

        with self._get_auth_session() as s:

            params = {"all": "true"}
            if folder_id:
                params["folder"] = folder_id

            if search_field:
                params["searchFields"] = search_field
                params["searchItem"] = search_item
                del params["all"]

                if search_field == "folder_name":
                    params["searchFields"] = "analysis_name"

            if project_id:
                params["projectId"] = project_id

            if plate_name:
                params["plateName"] = plate_name

            analyses = s.get(
                f"{URL}/{analysis_id}" if analysis_id else URL, params=params
            )

            if analyses.status_code != 200:
                raise ValueError(
                    "Invalid request. Please check your parameters."
                )
            if not analysis_id:
                res = analyses.json()["data"]

            else:
                res = [analyses.json()["analysis"]]

            folders = []
            for entry in range(len(res)):
                if "tenant_id" in res[entry]:
                    del res[entry]["tenant_id"]

                if "parameter_file_path" in res[entry]:
                    # Simple lambda function to find the third occurrence of '/' in the raw file path
                    location = lambda s: len(s) - len(s.split("/", 3)[-1])

                    # Slicing the string from the location
                    res[entry]["parameter_file_path"] = res[entry][
                        "parameter_file_path"
                    ][location(res[entry]["parameter_file_path"]) :]

                if (
                    show_folders
                    and not analysis_id
                    and res[entry]["is_folder"]
                ):
                    folders.append(res[entry]["id"])

            # recursive solution to get analyses in folders
            for folder in folders:
                res += self.get_analysis(folder_id=folder)

            if analysis_only:
                res = [
                    analysis for analysis in res if not analysis["is_folder"]
                ]
            return res

    def get_analysis_result_protein_data(
        self, analysis_id: str, link: bool = False, pg: str = None
    ):
        """
        Given an analysis id, this function returns the protein data for the analysis.

        Parameters
        ----------

        analysis_id : str
            ID of the analysis for which the data is to be fetched.
        link : bool
            Boolean flag denoting whether the user wants the default protein data. Defaults to False.
        pg : str
            Protein group ID to filter dataframe results. Defaults to None.

        """
        with self._get_auth_session() as s:
            URL = f"{self._auth.url}api/v1/data"
            response = s.get(
                f"{URL}/protein?analysisId={analysis_id}&retry=false"
            )

            if response.status_code != 200:
                raise ValueError(
                    "Could not fetch protein data. Please verify that your analysis completed."
                )
            response = response.json()

            protein_data = {}
            for row in response:
                if row.get("name") == "npLink":
                    protein_data["npLink"] = {
                        "url": row.get("link", {}).get("url", "")
                    }
                if row.get("name") == "panelLink":
                    protein_data["panelLink"] = {
                        "url": row.get("link", {}).get("url", "")
                    }
            if not protein_data:
                raise ValueError("No protein result files found.")
            if not "panelLink" in protein_data.keys():
                protein_data["panelLink"] = {"url": ""}

            if link:
                return protein_data
            else:
                if not pg:
                    return {
                        "protein_np": url_to_df(protein_data["npLink"]["url"]),
                        "protein_panel": url_to_df(
                            protein_data["panelLink"]["url"]
                        ),
                    }
                else:
                    protein_np = url_to_df(
                        protein_data["npLink"]["url"]
                    ).query(f"`Protein Group` == '{pg}'")
                    protein_panel = url_to_df(
                        protein_data["panelLink"]["url"]
                    ).query(f"`Protein Group` == '{pg}'")

                    if protein_np.empty and protein_panel.empty:
                        raise ValueError(
                            f"Protein group {pg} not found in analysis {analysis_id}."
                        )

                    return {
                        "protein_np": protein_np,
                        "protein_panel": protein_panel,
                    }

    def get_analysis_result_peptide_data(
        self, analysis_id: str, link: bool = False, peptide: str = None
    ):
        """
        Given an analysis id, this function returns the peptide data for the analysis.

        Parameters
        ----------

        analysis_id : str
            ID of the analysis for which the data is to be fetched.

        link : bool
            Boolean flag denoting whether the user wants the default peptide data. Defaults to False.

        peptide : str
            Peptide sequence to filter dataframe results. Defaults to None.

        """

        with self._get_auth_session() as s:
            URL = f"{self._auth.url}api/v1/data"
            response = s.get(
                f"{URL}/peptide?analysisId={analysis_id}&retry=false"
            )

            if response.status_code != 200:
                raise ValueError(
                    "Could not fetch peptide data. Please verify that your analysis completed."
                )

            response = response.json()

            peptide_data = {}
            for row in response:
                if row.get("name") == "npLink":
                    peptide_data["npLink"] = {
                        "url": row.get("link", {}).get("url", "")
                    }
                if row.get("name") == "panelLink":
                    peptide_data["panelLink"] = {
                        "url": row.get("link", {}).get("url", "")
                    }
            if not peptide_data:
                raise ValueError("No peptide result files found.")
            if not "panelLink" in peptide_data.keys():
                peptide_data["panelLink"] = {"url": ""}
            if link:
                return peptide_data
            else:
                if not peptide:
                    return {
                        "peptide_np": url_to_df(peptide_data["npLink"]["url"]),
                        "peptide_panel": url_to_df(
                            peptide_data["panelLink"]["url"]
                        ),
                    }
                else:
                    peptide_np = url_to_df(
                        peptide_data["npLink"]["url"]
                    ).query(f"Peptide == '{peptide}'")
                    peptide_panel = url_to_df(
                        peptide_data["panelLink"]["url"]
                    ).query(f"Peptide == '{peptide}'")

                    if peptide_np.empty and peptide_panel.empty:
                        raise ValueError(
                            f"Peptide {peptide} not found in analysis {analysis_id}."
                        )

                    return {
                        "peptide_np": peptide_np,
                        "peptide_panel": peptide_panel,
                    }

    def list_analysis_result_files(self, analysis_id: str):
        """
        Given an analysis id, this function returns a list of files associated with the analysis.

        Parameters
        ----------
        analysis_id : str
            ID of the analysis for which the data is to be fetched.

        Returns
        -------
        files: list
            List of files associated with the analysis.
        """
        try:
            analysis_metadata = self.get_analysis(analysis_id)[0]
        except (IndexError, ServerError):
            raise ValueError("Invalid analysis ID.")
        except:
            raise ValueError("Could not fetch analysis metadata.")

        if analysis_metadata.get("status") in ["Failed", None]:
            raise ValueError("Cannot find files for a failed analysis.")
        with self._get_auth_session() as s:
            response = s.get(
                f"{self._auth.url}api/v2/analysisResultFiles/{analysis_id}"
            )
            if response.status_code != 200:
                raise ServerError(
                    "Could not fetch analysis result files. Please verify that your analysis completed."
                )
            response = response.json()
            files = []
            for row in response["data"]:
                files.append(row["filename"])
            return files

    def get_analysis_result_file_url(self, analysis_id: str, filename: str):
        """
        Given an analysis id and a analysis result filename, this function returns the signed URL for the file.

        Parameters
        ----------
        analysis_id : str
            ID of the analysis for which the data is to be fetched.

        filename : str
            Name of the file to be fetched.

        Returns
        -------
        file_url: dict
            Response object containing the url for the file.
        """

        # Allow user to pass in filenames without an extension.
        analysis_result_files = self.list_analysis_result_files(analysis_id)
        analysis_result_files_prefix_mapper = {
            ".".join(x.split(".")[:-1]): x for x in analysis_result_files
        }
        if filename in analysis_result_files_prefix_mapper:
            filename = analysis_result_files_prefix_mapper[filename]

        analysis_metadata = self.get_analysis(analysis_id)[0]
        if analysis_metadata.get("status") in ["Failed", None]:
            raise ValueError("Cannot generate links for failed analyses.")
        with self._get_auth_session() as s:
            file_url = s.post(
                f"{self._auth.url}api/v1/analysisResultFiles/getUrl",
                json={
                    "analysisId": analysis_id,
                    "projectId": analysis_metadata["project_id"],
                    "filename": filename,
                },
            )
        response = file_url.json()
        if not response.get("url"):
            raise ValueError(f"File {filename} not found.")
        return response

    def get_analysis_result_files(
        self,
        analysis_id: str,
        filenames: _List[str],
        download_path: str = "",
        protein_all: bool = False,
        peptide_all: bool = False,
    ):
        """
        Given an analysis id and a list of file names, this function returns the file in form of downloadable content, if applicable.

        Parameters
        ----------
        analysis_id : str
            ID of the analysis for which the data is to be fetched.

        filenames : list
            List of filenames to be fetched. Only csv and tsv files are supported.

        download_path : str
            String flag denoting where the user wants the files downloaded. Can be local or absolute as long as the path is valid. Defaults to an empty string.

        protein_all : bool
            Boolean flag denoting whether the user wants the default protein data. Defaults to False.

        peptide_all : bool
            Boolean flag denoting whether the user wants the default peptide data. Defaults to False.

        Returns
        -------
        links: dict
            Contains dataframe objects for the requested files. If a filename is not found, it is skipped.


        Examples
        -------
        >>> from seer_pas_sdk import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> analysis_id = "YOUR_ANALYSIS_ID_HERE"
        >>> filenames = ["protein_np.tsv", "peptide_np.tsv"]
        >>> seer_sdk.get_analysis_result_files(analysis_id, filenames)
            {
                "protein_np.tsv": <protein_np dataframe object>,
                "peptide_np.tsv": <peptide_np dataframe object>
            }
        >>> seer_sdk.get_analysis_result_files(analysis_id, [], protein_all=True, peptide_all=True)
            {
                "protein_np.tsv": <protein_np dataframe object>,
                "protein_panel.tsv": <protein_panel dataframe object>,
                "peptide_np.tsv": <peptide_np dataframe object>,
                "peptide_panel.tsv": <peptide_panel dataframe object>
            }
        >>> seer_sdk.get_analysis_result_files(analysis_id, ["report.tsv"], download_path="/Users/Downloads")
            { "report.tsv": <report.tsv dataframe object> }
        """

        if not analysis_id:
            raise ValueError("Analysis ID cannot be empty.")

        if download_path and not os.path.exists(download_path):
            raise ValueError(
                "Please specify a valid folder path as download path."
            )

        links = {}
        if protein_all:
            protein_data = self.get_analysis_result_protein_data(
                analysis_id, link=True
            )
            links["protein_np.tsv"] = protein_data["npLink"]["url"]
            links["protein_panel.tsv"] = protein_data["panelLink"]["url"]
        if peptide_all:
            peptide_data = self.get_analysis_result_peptide_data(
                analysis_id, link=True
            )
            links["peptide_np.tsv"] = peptide_data["npLink"]["url"]
            links["peptide_panel.tsv"] = peptide_data["panelLink"]["url"]

        filenames = set(filenames)
        # Allow user to pass in filenames without an extension.
        analysis_result_files = self.list_analysis_result_files(analysis_id)
        analysis_result_files_prefix_mapper = {
            ".".join(x.split(".")[:-1]): x for x in analysis_result_files
        }
        for filename in filenames:
            if filename in analysis_result_files_prefix_mapper:
                filename = analysis_result_files_prefix_mapper[filename]
            if filename == "protein_np.tsv":
                if protein_all:
                    continue
                protein_data = self.get_analysis_result_protein_data(
                    analysis_id, link=True
                )
                links["protein_np.tsv"] = protein_data["npLink"]["url"]
            elif filename == "protein_panel.tsv":
                if protein_all:
                    continue
                protein_data = self.get_analysis_result_protein_data(
                    analysis_id, link=True
                )
                links["protein_panel.tsv"] = protein_data["panelLink"]["url"]
            elif filename == "peptide_np.tsv":
                if peptide_all:
                    continue
                peptide_data = self.get_analysis_result_peptide_data(
                    analysis_id, link=True
                )
                links["peptide_np.tsv"] = peptide_data["npLink"]["url"]
            elif filename == "peptide_panel.tsv":
                if peptide_all:
                    continue
                peptide_data = self.get_analysis_result_peptide_data(
                    analysis_id, link=True
                )
                links["peptide_panel.tsv"] = peptide_data["panelLink"]["url"]
            else:
                try:
                    links[filename] = self.get_analysis_result_file_url(
                        analysis_id, filename
                    )["url"]
                except Exception as e:
                    print(e)
                    continue

        links = {
            k: url_to_df(v, is_tsv=k.endswith(".tsv"))
            for k, v in links.items()
        }
        if download_path:
            name = f"{download_path}/downloads/{analysis_id}"
            print(f"Start download to path {name}")
            if not os.path.exists(name):
                os.makedirs(name)
            for filename, content in links.items():
                separator = ","
                if filename.endswith(".tsv"):
                    separator = "\t"
                content.to_csv(f"{name}/{filename}", sep=separator)
            print("Download complete.")

        return links

    def get_analysis_result(
        self,
        analysis_id: str,
        download_path: str = "",
        diann_report: bool = False,
    ):
        """
        Given an `analysis_id`, this function returns all relevant analysis data files in form of downloadable content, if applicable.

        Parameters
        ----------
        analysis_id : str
            ID of the analysis for which the data is to be fetched.

        download_path : str
            String flag denoting where the user wants the files downloaded. Can be local or absolute as long as the path is valid. Defaults to an empty string.

        diann_report : bool
            Boolean flag denoting whether the user wants the DIANN report to be included in the response. Defaults to False.

        Returns
        -------
        links: dict
            Contains dataframe objects for the `analysis_id`, given that the analysis has been complete.

        Examples
        -------
        >>> from seer_pas_sdk import SeerSDK
        >>> seer_sdk = SeerSDK()

        >>> seer_sdk.get_analysis_result("YOUR_ANALYSIS_ID_HERE")
        >>> {
                "peptide_np": <peptide_np dataframe object>,
                "peptide_panel": <peptide_panel dataframe object>,
                "protein_np": <protein_np dataframe object>,
                "protein_panel": <protein_panel dataframe object>
            }

        >>> seer_sdk.get_analysis_result("YOUR_DIANN_ANALYSIS_ID_HERE")
        >>> {
                "peptide_np": <peptide_np dataframe object>,
                "peptide_panel": <peptide_panel dataframe object>,
                "protein_np": <protein_np dataframe object>,
                "protein_panel": <protein_panel dataframe object>,
                "diann_report": <report.tsv dataframe object>
            }

        >>> seer_sdk.get_analysis_result("YOUR_ANALYSIS_ID_HERE", download_path="/Users/Downloads")
        >>> { "status": "Download complete." }
        """

        if not analysis_id:
            raise ValueError("Analysis ID cannot be empty.")

        if download_path and not os.path.exists(download_path):
            raise ValueError("The download path you entered is invalid.")

        protein_data = self.get_analysis_result_protein_data(
            analysis_id, link=True
        )
        peptide_data = self.get_analysis_result_peptide_data(
            analysis_id, link=True
        )
        links = {
            "peptide_np": url_to_df(peptide_data["npLink"]["url"]),
            "peptide_panel": url_to_df(peptide_data["panelLink"]["url"]),
            "protein_np": url_to_df(protein_data["npLink"]["url"]),
            "protein_panel": url_to_df(protein_data["panelLink"]["url"]),
        }

        if diann_report:
            diann_report_url = self.get_analysis_result_file_url(
                analysis_id, "report.tsv"
            )
            links["diann_report"] = url_to_df(diann_report_url["url"])

        if download_path:
            name = f"{download_path}/downloads/{analysis_id}"
            if not os.path.exists(name):
                os.makedirs(name)

            links["peptide_np"].to_csv(f"{name}/peptide_np.csv", sep="\t")
            links["peptide_panel"].to_csv(
                f"{name}/peptide_panel.csv", sep="\t"
            )
            links["protein_np"].to_csv(f"{name}/protein_np.csv", sep="\t")
            links["protein_panel"].to_csv(
                f"{name}/protein_panel.csv", sep="\t"
            )

            if "diann_report" in links:
                links["diann_report"].to_csv(
                    f"{name}/diann_report.csv", sep="\t"
                )

            return {"status": "Download complete."}

        return links

    def analysis_complete(self, analysis_id: str):
        """
        Returns the status of the analysis with the given id.

        Parameters
        ----------
        analysis_id : str
            The analysis id.

        Returns
        -------
        res : dict
            A dictionary containing the status of the analysis.

        Examples
        -------
        >>> from seer_pas_sdk import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.analysis_complete("YOUR_ANALYSIS_ID_HERE")
        >>> {
                "status": "SUCCEEDED"
            }
        """

        if not analysis_id:
            raise ValueError("Analysis id cannot be empty.")

        try:
            res = self.get_analysis(analysis_id)
        except ValueError:
            return ValueError("Analysis not found. Your ID could be incorrect")

        return {"status": res[0]["status"]}

    def list_ms_data_files(self, folder="", space=None):
        """
        Lists all the MS data files in the given folder as long as the folder path passed in the params is valid.

        Parameters
        ----------
        folder : str, optional
            Folder path to list the files from. Defaults to an empty string and displays all files for the user.
        space : str, optional
            ID of the user group to which the files belong, defaulted to None.

        Returns
        -------
        list
            Contains the list of files in the folder.

        Examples
        -------
        >>> from seer_pas_sdk import SeerSDK
        >>> sdk = SeerSDK()
        >>> folder_path = "test-may-2/"
        >>> sdk.list_ms_data_files(folder_path)
        >>> [
            "test-may-2/EXP20028/EXP20028_2020ms0096X10_A.raw",
            "test-may-2/agilent/05_C2_19ug-r001.d.zip",
            "test-may-2/agilent/08_BC_24ug-r001.d.zip",
            "test-may-2/d.zip/EXP22023_2022ms0143bX10_A_GA2_1_6681.d/EXP22023_2022ms0143bX10_A_GA2_1_6681.d.zip",
            "test-may-2/DIA/EXP20002_2020ms0142X10_A.wiff",
            "test-may-2/DIA/EXP20002_2020ms0142X10_A.wiff.scan",
            "test-may-2/DIA/EXP20002_2020ms0142X17_A.wiff",
            "test-may-2/DIA/EXP20002_2020ms0142X17_A.wiff.scan",
            "test-may-2/DIA/EXP20002_2020ms0142X18_A.wiff",
            "test-may-2/DIA/EXP20002_2020ms0142X18_A.wiff.scan"
        ]
        """

        URL = (
            f"{self._auth.url}api/v1/msdataindex/filesinfolder?folder={folder}"
            if not space
            else f"{self._auth.url}api/v1/msdataindex/filesinfolder?folder={folder}&userGroupId={space}"
        )
        with self._get_auth_session() as s:

            files = s.get(URL)

            if files.status_code != 200:
                raise ValueError(
                    "Invalid request. Please check your parameters."
                )
            return files.json()["filesList"]

    def download_ms_data_files(
        self, paths: _List[str], download_path: str, space: str = None
    ):
        """
        Downloads all MS data files for paths passed in the params to the specified download path.

        Parameters
        ----------
        paths : list[str]
            List of paths to download.
        download_path : str
            Path to download the files to.
        space : str, optional
            ID of the user group to which the files belongs, defaulted to None.

        Returns
        -------
        message: dict
            Contains the message whether the files were downloaded or not.
        """

        urls = []

        if not download_path:
            download_path = os.getcwd()
            print(f"\nDownload path not specified.\n")

        if not os.path.isdir(download_path):
            print(
                f'\nThe path "{download_path}" you specified does not exist, was either invalid or not absolute.\n'
            )
            download_path = f"{os.getcwd()}/downloads"

        name = (
            download_path if download_path[-1] != "/" else download_path[:-1]
        )

        if not os.path.exists(name):
            os.makedirs(name)

        print(f'Downloading files to "{name}"\n')

        URL = f"{self._auth.url}api/v1/msdataindex/download/getUrl"
        tenant_id = self._auth.active_tenant_id

        for path in paths:
            with self._get_auth_session() as s:

                download_url = s.post(
                    URL,
                    json={
                        "filepath": f"{tenant_id}/{path}",
                        "userGroupId": space,
                    },
                )

                if download_url.status_code != 200:
                    raise ValueError(
                        "Could not download file. Please check if the backend is running."
                    )
                urls.append(download_url.text)
        for i in range(len(urls)):
            filename = paths[i].split("/")[-1]
            url = urls[i]

            print(f"Downloading {filename}")

            for _ in range(2):
                try:
                    with tqdm(
                        unit="B",
                        unit_scale=True,
                        unit_divisor=1024,
                        miniters=1,
                        desc=f"Progress",
                    ) as t:
                        ssl._create_default_https_context = (
                            ssl._create_unverified_context
                        )
                        urllib.request.urlretrieve(
                            url,
                            f"{name}/{filename}",
                            reporthook=download_hook(t),
                            data=None,
                        )
                        break
                except:
                    filename = filename.split("/")
                    name += "/" + "/".join(
                        [filename[i] for i in range(len(filename) - 1)]
                    )
                    filename = filename[-1]
                    if not os.path.isdir(f"{name}/{filename}"):
                        os.makedirs(f"{name}/")

            else:
                raise ValueError(
                    "Your download failed. Please check if the backend is still running."
                )

            print(f"Finished downloading {filename}\n")

        return {"message": f"Files downloaded successfully to '{name}'"}

    def get_group_analysis(
        self, analysis_id, group_analysis_id=None, **kwargs
    ):
        """
        Returns the list of group analysis objects for the given analysis id, provided they exist.

        Parameters
        ----------
        analysis_id : str
            The analysis id.

        group_analysis_id : str, optional
            The group analysis id, defaulted to None. If provided, the function will return the group analysis object for the given group analysis id.

        **kwargs : dict, optional
            Search keyword parameters to be passed in. Acceptable values are 'name' or 'description'.

        """
        params = {"analysisid": analysis_id}
        if kwargs and not group_analysis_id:
            if len(kwargs.keys()) > 1:
                raise ValueError("Please include only one search parameter.")
            search_field = list(kwargs.keys())[0]
            if search_field not in ["name", "description"]:
                raise ValueError(
                    "Invalid search field. Please choose between 'name' or 'description'."
                )
            search_item = kwargs[search_field]

            if not search_item:
                raise ValueError(
                    f"Please provide a non null value for {search_field}"
                )
            params["searchFields"] = search_field
            params["searchItem"] = search_item

        URL = f"{self._auth.url}api/v1/groupanalysis/groupanalyses"

        if group_analysis_id:
            URL = f"{URL}/{group_analysis_id}"
            params["id"] = group_analysis_id

        with self._get_auth_session() as s:
            response = s.get(URL, params=params)
            if response.status_code != 200:
                raise ServerError(
                    "Request failed. Please check your parameters."
                )
            response = response.json()
            return response

    def group_analysis_results(self, analysis_id: str, group_analysis_id=None):
        """
        Returns the group analysis data for the given analysis id, provided it exists.

        If no group analysis id is provided, the function will return the most recent group analysis data for the given analysis id.

        Parameters
        ----------
        analysis_id : str
            The analysis id.

        group_analysis_id : str, optional
            The group analysis id, defaulted to None.

        Returns
        -------
        res : dict
            A dictionary containing the group analysis data.

        Examples
        -------
        >>> from seer_pas_sdk import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.group_analysis_results("YOUR_ANALYSIS_ID_HERE")
        >>> {
                "pre": {
                    "protein": [],
                    "peptide": [],
                },
                "post": {
                    "protein": {},
                    "protein_url": {
                        "protein_processed_file_url": "",
                        "protein_processed_long_form_file_url": "",
                    },
                    "peptide": {},
                    "peptide_url": {
                        "peptide_processed_file_url": "",
                        "peptide_processed_long_form_file_url": "",
                    },
                },
                "box_plot": []
            }
        """

        if not analysis_id:
            raise ValueError("Analysis ID cannot be empty.")

        URL = f"{self._auth.url}"

        res = {
            "pre": {
                "protein": [],
                "peptide": [],
            },
            "post": {
                "protein": {},
                "protein_url": {
                    "protein_processed_file_url": "",
                    "protein_processed_long_form_file_url": "",
                },
                "peptide": {},
                "peptide_url": {
                    "peptide_processed_file_url": "",
                    "peptide_processed_long_form_file_url": "",
                },
            },
        }

        # Pre-GA data call
        with self._get_auth_session() as s:

            protein_pre_data = s.post(
                url=f"{URL}api/v2/groupanalysis/protein",
                json={"analysisId": analysis_id, "grouping": "condition"},
            )
            if protein_pre_data.status_code != 200:
                raise ServerError(
                    "Invalid request. Could not fetch group analysis protein pre data. Please check your parameters."
                )

            protein_pre_data = protein_pre_data.json()

            res["pre"]["protein"] = protein_pre_data

        with self._get_auth_session() as s:

            peptide_pre_data = s.post(
                url=f"{URL}api/v2/groupanalysis/peptide",
                json={"analysisId": analysis_id, "grouping": "condition"},
            )

            if peptide_pre_data.status_code != 200:
                raise ServerError(
                    "Invalid request. Could not fetch group analysis peptide pre data. Please check your parameters."
                )

            peptide_pre_data = peptide_pre_data.json()
            res["pre"]["peptide"] = peptide_pre_data

        # Post-GA data call
        with self._get_auth_session() as s:
            if group_analysis_id:
                get_saved_result = self.get_group_analysis(
                    analysis_id=analysis_id,
                    group_analysis_id=group_analysis_id,
                )
            else:
                get_saved_result = s.get(
                    f"{URL}api/v1/groupanalysis/getSavedResults?analysisid={analysis_id}"
                )
                if get_saved_result.status_code != 200:
                    raise ServerError(
                        "Could not fetch saved results. Please check your analysis id."
                    )
                get_saved_result = get_saved_result.json()

            # Protein data
            if "pgResult" in get_saved_result:
                res["post"]["protein"] = get_saved_result["pgResult"]

            # Peptide data
            if "peptideResult" in get_saved_result:
                res["post"]["peptide"] = get_saved_result["peptideResult"]

            # require that either protein or peptide data exists
            # Error handling is necessary for volcano plot calculations downstream
            if not (res["post"].get("protein") or res["post"].get("peptide")):
                raise ValueError(
                    "No group analysis data returned from server."
                )

            # Protein URLs
            if "pgProcessedFileUrl" in get_saved_result:
                res["post"]["protein_url"]["protein_processed_file_url"] = (
                    get_saved_result["pgProcessedFileUrl"]
                )
            if "pgProcessedLongFormFileUrl" in get_saved_result:
                res["post"]["protein_url"][
                    "protein_processed_long_form_file_url"
                ] = get_saved_result["pgProcessedLongFormFileUrl"]

            # Peptide URLs
            if "peptideProcessedFileUrl" in get_saved_result:
                res["post"]["peptide_url"]["peptide_processed_file_url"] = (
                    get_saved_result["peptideProcessedFileUrl"]
                )

            if "peptideProcessedLongFormFileUrl" in get_saved_result:
                res["post"]["peptide_url"][
                    "peptide_processed_long_form_file_url"
                ] = get_saved_result["peptideProcessedLongFormFileUrl"]

        return res

    def get_box_plot_data(
        self,
        analysis_id: str,
        group_analysis_id: str = None,
        feature_ids: _List[str] = [],
        show_significant_only: bool = False,
        as_df=False,
        volcano_plot=False,
        cached=False,
    ):
        """Get box plot data for given analyses and samples formatted in a DataFrame or a dictionary.

        Args:
            analysis_id (str): ID of the analysis.
            feature_ids (list[str], optional): Filter result object to a set of ids. Defaults to [].
            show_significant_only (bool, optional): Mark true if only significant results are to be returned. Defaults to False.
            as_df (bool, optional): Mark true if return object should be a pandas DataFrame. Defaults to False.
            volcano_plot (bool, optional): Mark true to include the volcano plot data in the return object. Defaults to False.
            cached (bool, optional): Mark true to return volcano plot data as a VolcanoPlotBuilder object. No effect if volcano_plot flag is marked false. Defaults to False.

        Raises:
            ValueError: Invalid feature type. Must be either 'protein' or 'peptide'.
            ServerError: Could not fetch box plot data.

        Returns:
            list[dict] | pd.DataFrame : A list of dictionaries or a dataframe with each row containing the following keys/columns:
                                        'proteinId', 'intensity', 'sampleName', 'sampleId', 'condition','gene'
        """

        with self._get_auth_session() as s:

            # API call 1 - get volcano plot data for filtered results and gene mapping
            builder = self.get_volcano_plot_data(
                analysis_id, cached=True, group_analysis_id=group_analysis_id
            )

            protein_peptide_gene_map = builder.protein_gene_map

            # API call 2 - get analysis samples metadata to get condition
            samples_metadata = self.get_analysis_samples(analysis_id)

            json = {"analysisId": analysis_id}
            if feature_ids:
                json["featureIds"] = ",".join(feature_ids)
            filters = ""
            # API call 3 - get group analysis data. This gives us the filters for the group analysis
            if group_analysis_id:
                ga = self.get_group_analysis(
                    analysis_id, group_analysis_id=group_analysis_id
                )
                filters = ga["parameters"]["filters"]
            if filters:
                json["filters"] = filters

            json["featureType"] = (
                builder.type if builder.type == "peptide" else "proteingroup"
            )

            # API call 4 - get intensities
            box_plot_data = s.post(
                url=f"{self._auth.url}api/v1/groupanalysis/rawdata", json=json
            )

            if box_plot_data.status_code != 200:
                raise ServerError("Could not fetch box plot data.")

            box_plot_data = box_plot_data.json()
            feature_type_index = (
                "peptide" if builder.type == "peptide" else "proteinId"
            )
            box_plot_data = [
                x
                for x in box_plot_data
                if x[feature_type_index] in protein_peptide_gene_map
            ]
            sample_id_condition = {
                x["id"]: x["condition"] for x in samples_metadata[0]["samples"]
            }

            if show_significant_only:
                significant_rows = set(builder.get_significant_rows())
                box_plot_data = [
                    x
                    for x in box_plot_data
                    if x[feature_type_index] in significant_rows
                ]

            for row in box_plot_data:
                row["condition"] = sample_id_condition.get(
                    row["sampleId"], None
                )
                row["gene"] = builder.protein_gene_map[row[feature_type_index]]

            if as_df:
                box_plot_data = pd.DataFrame(box_plot_data)

            if volcano_plot:
                vplot = None
                if cached:
                    vplot = builder
                elif as_df:
                    vplot = pd.DataFrame(builder.volcano_plot)
                else:
                    vplot = builder.volcano_plot

                return {"box_plot": box_plot_data, "volcano_plot": vplot}
            return box_plot_data

    def get_all_volcano_plot_data(self, analysis_id: str, box_plot=False):
        """
        Get all volcano plot data for a given analysis.

        Args:
            analysis_id (str): ID of the analysis.
            box_plot (bool, optional): Mark true to include box plot data in the return object. Defaults to False.

        Returns:
            dict: A dictionary containing the volcano plot and optionally box plot data for each group analysis.
        """
        group_analysis_ids = [
            x["id"]
            for x in self.get_group_analysis(analysis_id).get("data", [])
            if x.get("id")
        ]
        if not group_analysis_ids:
            return {}
        results = dict()

        if box_plot:
            results = {
                ga_id: {
                    k: v
                    for k, v in self.get_box_plot_data(
                        analysis_id, ga_id, as_df=True, volcano_plot=True
                    ).items()
                }
                for ga_id in group_analysis_ids
            }
        else:
            results = {
                ga_id: {
                    "volcano_plot": self.get_volcano_plot_data(
                        analysis_id, group_analysis_id=ga_id, as_df=True
                    )
                }
                for ga_id in group_analysis_ids
            }

        return results

    def _get_analysis_pca(
        self,
        analysis_ids: _List[str],
        sample_ids: _List[str],
        type: str,
        hide_control: bool = False,
    ):
        """
        ****************
        [UNEXPOSED METHOD CALL]
        ****************
        Get PCA data for given analyses and samples.
        Args:
            analysis_ids (list[str]): IDs of the analyses of interest.
            sample_ids (list[str]): IDs of the samples of interest.
            type (str): Type of data to be fetched. Must be either 'protein' or 'peptide'.
            hide_control (bool, optional): Mark true if controls are to be excluded. Defaults to False.
        Raises:
            ValueError: No analysis IDs provided.
            ValueError: No sample IDs provided.
            ValueError: Invalid type provided.
            ServerError: Could not fetch PCA data.
        Returns:
            dict
                Pure response from the API.
        """
        if not analysis_ids:
            raise ValueError("Analysis IDs cannot be empty.")
        if type not in ["protein", "peptide"]:
            raise ValueError("Type must be either 'protein' or 'peptide'.")

        URL = f"{self._auth.url}api/v1/analysisqcpca"

        with self._get_auth_session() as s:
            json = {
                "analysisIds": ",".join(analysis_ids),
                "type": type,
            }
            if sample_ids:
                json["sampleIds"] = ",".join(sample_ids)

            # specify hideControl as a string - unexpected behavior occurs if a boolean is passed
            if hide_control:
                json["hideControl"] = "true"
            else:
                json["hideControl"] = "false"

            pca_data = s.post(URL, json=json)

            if pca_data.status_code != 200:
                raise ServerError("Could not fetch PCA data.")

            return pca_data.json()

    def get_analysis_pca_data(
        self,
        analysis_ids: _List[str],
        type: str,
        sample_ids: _List[str] = [],
        hide_control: bool = False,
        as_df=False,
    ):
        """
        Get PCA data for given analyses and samples formatted in a DataFrame or a dictionary.
        Args:
            analysis_ids (list[str]): IDs of the analyses of interest.
            type (str): Type of data to be fetched. Must be either 'protein' or 'peptide'.
            sample_ids (list[str], optional): IDs of the samples of interest.
            hide_control (bool, optional): Mark true if controls are to be excluded. Defaults to False.
            as_df (bool, optional): Mark true if the data should be returned as a pandas DataFrame. Defaults to False.
        Raises:
            ValueError: No analysis IDs provided.
            ValueError: No sample IDs provided.
            ValueError: Invalid type parameter provided.
            ServerError: Could not fetch PCA data.
        Returns:
            A dictionary with the following keys:
                - x_contribution_ratio (float): Proportion of variance explained by the x-axis.
                - y_contribution_ratio (float): Proportion of variance explained by the y-axis.
                - data (list[dict] | pd.DataFrame): A list of dictionaries or a dataframe with each row containing the following keys/columns:
                    - sample_name (str): Name of the sample.
                    - plate_name (str): Name of the plate.
                    - sample_id (int): ID of the sample.
                    - condition (str): Condition.
                    - PC1 (float): X-value of the PCA point.
                    - PC2 (float): Y-value of the PCA point.
                    - custom_* (str): Custom fields. Included if meaningful, i.e., not null, in the data.
        Examples
        --------
        >>> from seer_pas_sdk import *
        >>> sdk = SeerSDK()
        >>> sdk.get_analysis_pca_data(
                analysis_ids=["analysis_id"],
                sample_ids=["sample_id"],
                type="protein",
                hide_control=False
            )
        """
        pca_data = self._get_analysis_pca(
            analysis_ids, sample_ids, type, hide_control
        )

        # common columns returned by the API
        generic_columns = [
            "sample_name",
            "plate_name",
            "sample_id",
            "condition",
            "PC1",
            "PC2",
        ]

        # edge case where yContributionRatio is NaN when zero points are returned.
        if not "yContributionRatio" in pca_data:
            y_contribution_ratio = None
        else:
            y_contribution_ratio = pca_data["yContributionRatio"]

        x_contribution_ratio = pca_data["xContributionRatio"]
        samples = pca_data["samples"]
        points = pca_data["points"]

        df = pd.DataFrame(
            [
                sample | {"PC1": point[0], "PC2": point[1]}
                for sample, point in zip(samples, points)
            ]
        )

        # Slice the df such that only custom columns are dropped in the absence of data
        df = pd.concat(
            [
                df.drop(columns=generic_columns).dropna(how="all", axis=1),
                df[generic_columns],
            ],
            axis=1,
        )

        # Filter down to a minimal set of columns
        permitted_columns = [
            x
            for x in df.columns
            if x in generic_columns or x.startswith("custom_")
        ]

        df = df.loc(axis=1)[permitted_columns]

        # Return the data as a DataFrame if as_df is True
        if not as_df:
            df = df.to_dict(orient="records")
        result = dict(
            x_contribution_ratio=x_contribution_ratio,
            y_contribution_ratio=y_contribution_ratio,
            data=df,
        )
        return result

    def get_analysis_hierarchical_clustering(
        self,
        analysis_ids: _List[str],
        sample_ids: _List[str] = [],
        hide_control: bool = False,
    ):
        """
        Get hierarchical clustering data for given analyses and samples.
        Args:
            analysis_ids (list[str]): IDs of the analyses.
            sample_ids (list[str], optional): IDs of the samples.
            hide_control (bool, optional): Mark true if controls are to be excluded. Defaults to False.
            raw_data (bool, optional): Mark true if raw data should be returned. Defaults to True.
        Raises:
            ValueError: No analysis IDs provided.
            ValueError: No sample IDs provided.
            ValueError: Response status code is not 200.
        Returns:
            dict
                Hierarchical clustering data returned by the API.
        """
        if not analysis_ids:
            raise ValueError("Analysis IDs cannot be empty.")

        URL = f"{self._auth.url}api/v1/analysishcluster"

        with self._get_auth_session() as s:
            json = {
                "analysisIds": ",".join(analysis_ids),
            }
            if sample_ids:
                json["sampleIds"] = ",".join(sample_ids)

            if sample_ids:
                json["sampleIds"] = ",".join(sample_ids)

            # specify hideControl as a string
            # Python bool values are not recognized by the API
            if hide_control:
                json["hideControl"] = "true"
            else:
                json["hideControl"] = "false"

            hc_data = s.post(URL, json=json)

            if hc_data.status_code != 200:
                raise ValueError(
                    "Invalid request. Please check your parameters."
                )

            data = hc_data.json()

            # Filter out custom fields that are not part of the tenant's custom fields
            if not "samples" in data:
                raise ValueError("No sample data returned from server.")

            data["samples"] = [
                {k: v for k, v in sample.items()} for sample in data["samples"]
            ]

            return data

    def get_ppi_network_data(
        self, significant_pgs: _List[str], species: str = None
    ):
        """
        Get PPI network data for given significant protein groups.
        Args:
            significant_pgs (_List[str]): Significant protein groups.
            species (str, optional): Species of interest. Defaults to None.
        Raises:
            ValueError: No significant protein groups provided.
            ValueError: Response status code is not 200.
        Returns:
            dict
                Response returned by the API.
        """
        if not significant_pgs:
            raise ValueError("Significant protein groups cannot be empty.")

        URL = f"{self._auth.url}api/v1/groupanalysis/stringdb"

        with self._get_auth_session() as s:
            json = {
                "significantPGs": ",".join(significant_pgs),
            }
            if species:
                json["species"] = species

            ppi_data = s.post(URL, json=json)

            if ppi_data.status_code != 200:
                raise ValueError("Server error - bad response")

            return ppi_data.json()

    # groups are user defined by the sample description file
    def get_cluster_heatmap_data(
        self,
        analysis_id: str,
        grouping: str,
        groups: _List[str],
        contrasts: _List[_Tuple[int, ...]],
        stat_test: str,
        feature_type: str,
        significant_pgs: _List[str] = [],
    ):
        """Get cluster heatmap data for the given analysis.

        Args:
            analysis_id (str): ID of the analysis
            grouping (str): Category of sample groups
            groups (_List[str]): sample groups
            contrasts (_List[_Tuple[int, ...]]): Indicate which groups are compared against each other. e.g. [(0, 1, -1, 0), (1, 0, 0, -1)]
            stat_test (str): Statistical test to be used
            feature_type (str): Type of feature to be used, either proteingroup or peptide
            significant_pgs (_List[str], optional): significant protein group IDs. Defaults to [].

        Raises:
            ValueError: "Feature type must be either 'proteingroup' or 'peptide'."
            ValueError: "Stat test must be either 'ttest' or 'wilcoxon'."
            ValueError: Invalid contrast value.
            ValueError: Server error

        Returns:
            dict: the response object
                    clusterProtein: List of protein clusters
                        clusters:
                            indexes: list[int], List of indexes
                            height: int, Height of the cluster
                            children: list[dict] | None, Children of the cluster
                    clusterSample: List of sample clusters
                        clusters:
                            indexes: list[int], List of indexes
                            height: int, Height of the cluster
                            children: list[dict] | None, Children of the cluster
                    data: List of data

        """
        if feature_type not in ["proteingroup", "peptide"]:
            raise ValueError(
                "Feature type must be either 'proteingroup' or 'peptide'."
            )

        if stat_test not in ["ttest", "wilcoxon"]:
            raise ValueError("Stat test must be either 'ttest' or 'wilcoxon'.")

        [validate_contrast(contrast, len(groups)) for contrast in contrasts]

        formatted_contrasts = ";".join(
            [",".join(map(str, x)) for x in contrasts]
        )

        payload = dict(
            analysisId=analysis_id,
            grouping=grouping,
            groups=",".join(groups),
            contrasts=formatted_contrasts,
            statTest=stat_test,
            featureType=feature_type,
            significantPGs=",".join(significant_pgs),
        )

        with self._get_auth_session() as s:
            URL = f"{self._auth.url}api/v2/clusterheatmap"
            response = s.post(URL, json=payload)
            if response.status_code != 200:
                raise ValueError("Server error. Bad response.")
            return response.json()

    def get_enrichment_plot(
        self,
        analysis_id: str,
        significant_pgs: _List[str],
        summarize_output: bool = False,
        exclude_singleton: bool = False,
        cutoff: float = None,
        species: str = None,
    ):
        """
        Get enrichment plot data for a given analysis ID.

        Args:
            analysis_id (str): ID of the analysis.
            significant_pgs (_List[str]): List of significant protein/peptide groups.
            summarize_output (bool, optional): Summarize the output. Defaults to False.
            exclude_singleton (bool, optional): Exclude singleton values. Defaults to False.
            cutoff (float, optional): Cutoff value for the p-value to determine significance. Defaults to None.
            species (str, optional): Species to filter the data by. Defaults to None.

        Raises:
            ServerError - could not fetch enrichment plot data.

        Returns:
            dict: A dictionary containing the enrichment plot data.
        """

        URL = f"{self._auth.url}api/v1/groupanalysis/enrichmentgo"

        if not significant_pgs:
            raise ValueError("Significant pgs cannot be empty.")

        with self._get_auth_session() as s:
            json = {
                "analysisId": analysis_id,
                "significantPGs": significant_pgs,
                "summarizeOutput": summarize_output,
                "excludeSingleton": exclude_singleton,
            }
            if cutoff:
                json["cutoff"] = cutoff
            if species:
                json["species"] = species

            enrichment_data = s.post(URL, json=json)

            if enrichment_data.status_code != 200:
                raise ValueError("Could not fetch enrichment plot data.")

            return enrichment_data.json()

    def get_volcano_plot_data(
        self,
        analysis_id,
        group_analysis_id=None,
        significance_threshold=0.05,
        fold_change_threshold=1,
        label_by="fold_change",
        cached=False,
        as_df=False,
    ):
        """Get volcano plot data for a given analysis ID.

        Args:
            analysis_id (str): ID of the analysis.
            significance_threshold (float, optional): Cutoff value for the p-value to determine significance. Defaults to 0.05.
            fold_change_threshold (float, optional): Cutoff value for the fold change to determine significance. Defaults to 1.
            label_by (str, optional): Metric to sort result data. Defaults to "fold_change".
            cached (bool, optional): Return a VolcanoPlotBuilder object for calculation reuse. Defaults to False.
            as_df (bool, optional): Return data as a pandas DataFrame. Defaults to False.

        Raises:
            ServerError - could not fetch group analysis results.
        Returns:
           list[dict] | pd.DataFrame | VolcanoPlotBuilder: A list of dictionaries, a DataFrame, or a VolcanoPlotBuilder object containing the volcano plot data.
                                                           Object contains the following columns: 'logFD', 'negativeLog10P', 'dataIndex', 'rowID', 'gene', 'protein',
                                                                                                   'group', 'significant', 'euclideanDistance'
        """
        try:
            response = self.group_analysis_results(
                analysis_id, group_analysis_id=group_analysis_id
            )
        except:
            raise ServerError(
                f"Could not fetch group analysis results. Please check that group analysis has completed for analysis {analysis_id}."
            )

        obj = VolcanoPlotBuilder(
            response, significance_threshold, fold_change_threshold, label_by
        )

        if cached:
            return obj
        else:
            if as_df:
                return pd.DataFrame(obj.volcano_plot)
            else:
                return obj.volcano_plot

    def get_analysis_samples(self, analysis_id: str):
        """
        Get the samples associated with a given analysis ID.

        Args:
            analysis_id (str): The analysis ID.

        Raises:
            ServerError - could not retrieve samples for analysis.
        Returns:
            dict: A dictionary containing the samples associated with the analysis.
        """
        if not analysis_id:
            raise ValueError("Analysis ID cannot be empty.")

        URL = f"{self._auth.url}api/v1/analyses/samples/{analysis_id}"
        with self._get_auth_session() as s:
            samples = s.get(URL)

            if samples.status_code != 200:
                raise ServerError("Could not retrieve samples for analysis.")

            return samples.json()

    def get_analysis_protocol_fasta(self, analysis_id, download_path=None):
        if not analysis_id:
            raise ValueError("Analysis ID cannot be empty.")

        if not download_path:
            download_path = os.getcwd()

        try:
            analysis_protocol_id = self.get_analysis(analysis_id)[0][
                "analysis_protocol_id"
            ]
        except (IndexError, KeyError):
            raise ValueError(f"Could not parse server response.")

        try:
            analysis_protocol_engine = self.get_analysis_protocols(
                analysis_protocol_id=analysis_protocol_id
            )[0]["analysis_engine"]
        except (IndexError, KeyError):
            raise ValueError(f"Could not parse server response.")

        analysis_protocol_engine = analysis_protocol_engine.lower()
        if analysis_protocol_engine == "diann":
            URL = f"{self._auth.url}api/v1/analysisProtocols/editableParameters/diann/{analysis_protocol_id}"
        elif analysis_protocol_engine == "encyclopedia":
            URL = f"{self._auth.url}api/v1/analysisProtocols/editableParameters/dia/{analysis_protocol_id}"
        elif analysis_protocol_engine == "msfragger":
            URL = f"{self._auth.url}api/v1/analysisProtocols/editableParameters/msfragger/{analysis_protocol_id}"
        elif analysis_protocol_engine == "proteogenomics":
            URL = f"{self._auth.url}api/v1/analysisProtocols/editableParameters/proteogenomics/{analysis_protocol_id}"
        else:
            # Change needed on the backend to get s3 file path for MaxQuant
            # URL = f"{self._auth.url}api/v1/analysisProtocols/editableParameters/{analysis_protocol_id}"
            raise ValueError(
                f"Analysis protocol engine {analysis_protocol_engine} not supported for fasta download."
            )

        with self._get_auth_session() as s:
            response = s.get(URL)
            if response.status_code != 200:
                raise ServerError("Request failed.")
            response = response.json()
            if type(response) == dict:
                response = response["editableParameters"]
            fasta_filenames = [
                x["Value"]
                for x in response
                if x["Key"] in ["fasta", "fastaFilePath", "referencegenome"]
            ]
            if not fasta_filenames:
                raise ServerError("No fasta file name returned from server.")

        URL = f"{self._auth.url}api/v1/analysisProtocolFiles/getUrl"
        for file in fasta_filenames:
            with self._get_auth_session() as s:
                response = s.post(URL, json={"filepath": file})
                if response.status_code != 200:
                    raise ServerError("Request failed.")
                url = response.json()["url"]
                filename = os.path.basename(file)
                print(f"Downloading {filename}")
                for _ in range(2):
                    try:
                        with tqdm(
                            unit="B",
                            unit_scale=True,
                            unit_divisor=1024,
                            miniters=1,
                            desc=f"Progress",
                        ) as t:
                            ssl._create_default_https_context = (
                                ssl._create_unverified_context
                            )
                            urllib.request.urlretrieve(
                                url,
                                f"{download_path}/{filename}",
                                reporthook=download_hook(t),
                                data=None,
                            )
                            break
                    except:
                        if not os.path.isdir(f"{download_path}"):
                            os.makedirs(f"{download_path}")

                print(f"Downloaded file to {download_path}/{file}")
