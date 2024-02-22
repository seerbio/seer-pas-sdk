from tqdm import tqdm

import os
import jwt
import requests
import urllib.request
import ssl
import shutil

from typing import List as _List

from ..common import *
from ..auth import Auth
from ..objects import PlateMap


class SeerSDK:
    """
    Object exposing SDK methods. Requires a username and password; the optional `instance` param denotes the instance of PAS (defaults to "US").

    Examples
    -------
    >>> from core import SeerSDK
    >>> USERNAME = "test"
    >>> PASSWORD = "test-password"
    >>> INSTANCE = "EU"
    >>> seer_sdk = SeerSDK(USERNAME, PASSWORD, INSTANCE)
    """

    def __init__(self, username, password, instance="US"):
        try:
            self._auth = Auth(username, password, instance)

            self._auth.get_token()

            print(f"User '{username}' logged in.\n")

        except:
            raise ValueError(
                "Could not log in.\nPlease check your credentials and/or instance."
            )

    def get_spaces(self):
        """
        Fetches a list of spaces for the authenticated user.

        Returns
        -------
        spaces: list
            List of space objects for the authenticated user.

        Examples
        -------
        >>> from core import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.get_spaces()
        >>> [
                { "usergroup_name": ... },
                { "usergroup_name": ... },
                ...
            ]
        """

        ID_TOKEN, ACCESS_TOKEN = self._auth.get_token()
        HEADERS = {
            "Authorization": f"{ID_TOKEN}",
            "access-token": f"{ACCESS_TOKEN}",
        }
        URL = f"{self._auth.url}api/v1/usergroups"

        with requests.Session() as s:
            s.headers.update(HEADERS)

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
        >>> from core import SeerSDK
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

        ID_TOKEN, ACCESS_TOKEN = self._auth.get_token()
        HEADERS = {
            "Authorization": f"{ID_TOKEN}",
            "access-token": f"{ACCESS_TOKEN}",
        }
        URL = f"{self._auth.url}api/v1/plates"
        res = []

        with requests.Session() as s:
            s.headers.update(HEADERS)

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
        >>> from core import SeerSDK
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

        ID_TOKEN, ACCESS_TOKEN = self._auth.get_token()
        HEADERS = {
            "Authorization": f"{ID_TOKEN}",
            "access-token": f"{ACCESS_TOKEN}",
        }
        URL = (
            f"{self._auth.url}api/v1/projects"
            if not project_id
            else f"{self._auth.url}api/v1/projects/{project_id}"
        )
        res = []

        with requests.Session() as s:
            s.headers.update(HEADERS)

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

    def _get_samples_metadata(
        self, plate_id: str = None, project_id: str = None, df: bool = False
    ):
        """
        ****************
        [UNEXPOSED METHOD CALL]
        ****************

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
        >>> from core import SeerSDK
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
        ID_TOKEN, ACCESS_TOKEN = self._auth.get_token()
        HEADERS = {
            "Authorization": f"{ID_TOKEN}",
            "access-token": f"{ACCESS_TOKEN}",
        }
        URL = f"{self._auth.url}api/v1/samples"
        sample_params = {"all": "true"}

        with requests.Session() as s:
            s.headers.update(HEADERS)

            if plate_id:
                try:
                    self.get_plate_metadata(plate_id)
                except:
                    raise ValueError(
                        "Plate ID is invalid. Please check your parameters and see if the backend is running."
                    )
                sample_params["plateId"] = plate_id

            elif project_id:
                try:
                    self.get_project_metadata(project_id)
                except:
                    raise ValueError(
                        "Project ID is invalid. Please check your parameters and see if the backend is running."
                    )

                sample_params["projectId"] = project_id

            samples = s.get(URL, params=sample_params)
            if samples.status_code != 200:
                raise ValueError(
                    "Invalid request. Please check if your plate ID has any samples associated with it."
                )
            res = samples.json()["data"]

            for entry in res:
                del entry["tenant_id"]

        return res if not df else dict_to_df(res)

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
        >>> from core import SeerSDK
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
        res = []
        for sample_id in sample_ids:
            ID_TOKEN, ACCESS_TOKEN = self._auth.get_token()
            HEADERS = {
                "Authorization": f"{ID_TOKEN}",
                "access-token": f"{ACCESS_TOKEN}",
            }
            URL = f"{self._auth.url}api/v1/msdatas/items"

            with requests.Session() as s:
                s.headers.update(HEADERS)

                msdatas = s.post(URL, json={"sampleId": sample_id})

                if msdatas.status_code != 200 or not msdatas.json()["data"]:
                    raise ValueError(
                        "Failed to fetch MS data for your plate ID."
                    )

                res.append(msdatas.json()["data"][0])

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
        >>> from core import SeerSDK
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
        self, project_id: str, msdata: bool = False, df: bool = False
    ):
        """
        Fetches samples (and MS data files) for a `project_id` (provided that the `project_id` is valid and has samples associated with it) for an authenticated user.

        The function returns a DataFrame object if the `df` flag is passed in as True, otherwise a nested dict object is returned instead. If the both the `df` and `msdata` flags are passed in as True, then a nested DataFrame object is returned instead.

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
        >>> from core import SeerSDK
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

        if msdata:
            sample_ids = [
                sample["id"] for sample in project_samples
            ]  # will always contain unique values
            ms_data_files = self.get_msdata(sample_ids=sample_ids, df=False)

            for ms_data_file in ms_data_files:
                for sample_index in range(len(project_samples)):
                    if (
                        project_samples[sample_index]["id"]
                        == ms_data_file["sample_id"]
                    ):
                        if "ms_data_file" not in project_samples[sample_index]:
                            project_samples[sample_index]["ms_data_files"] = [
                                ms_data_file
                            ]
                        else:
                            project_samples[sample_index][
                                "ms_data_files"
                            ].append(ms_data_file)

        if df:
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
        >>> from core import SeerSDK
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

        ID_TOKEN, ACCESS_TOKEN = self._auth.get_token()
        HEADERS = {
            "Authorization": f"{ID_TOKEN}",
            "access-token": f"{ACCESS_TOKEN}",
        }
        URL = (
            f"{self._auth.url}api/v1/analysisProtocols"
            if not analysis_protocol_id
            else f"{self._auth.url}api/v1/analysisProtocols/{analysis_protocol_id}"
        )
        res = []

        with requests.Session() as s:
            s.headers.update(HEADERS)

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

    def get_analysis(self, analysis_id: str = None):
        """
        Returns a list of analyses objects for the authenticated user. If no id is provided, returns all analyses for the authenticated user.

        Parameters
        ----------
        analysis_id : str, optional
            ID of the analysis to be fetched, defaulted to None.

        Returns
        -------
        analyses: dict
            Contains a list of analyses objects for the authenticated user.

        Examples
        -------
        >>> from core import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.get_analysis()
        >>> [
                {id: "YOUR_ANALYSIS_ID_HERE", ...},
                {id: "YOUR_ANALYSIS_ID_HERE", ...},
                {id: "YOUR_ANALYSIS_ID_HERE", ...}
            ]

        >>> seer_sdk.get_analyses("YOUR_ANALYSIS_ID_HERE")
        >>> [{ id: "YOUR_ANALYSIS_ID_HERE", ...}]
        """

        ID_TOKEN, ACCESS_TOKEN = self._auth.get_token()
        HEADERS = {
            "Authorization": f"{ID_TOKEN}",
            "access-token": f"{ACCESS_TOKEN}",
        }
        URL = f"{self._auth.url}api/v1/analyses"
        res = []

        with requests.Session() as s:
            s.headers.update(HEADERS)

            analyses = s.get(
                f"{URL}/{analysis_id}" if analysis_id else URL,
                params={"all": "true"},
            )
            if analyses.status_code != 200:
                raise ValueError(
                    "Invalid request. Please check your parameters."
                )
            if not analysis_id:
                res = analyses.json()["data"]

            else:
                res = [analyses.json()["analysis"]]

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

    def get_analysis_result(self, analysis_id: str, download_path: str = ""):
        """
        Given an `analysis_id`, this function returns all relevant analysis data files in form of downloadable content, if applicable.

        Parameters
        ----------
        analysis_id : str
            ID of the analysis for which the data is to be fetched.

        download_path : bool
            String flag denoting where the user wants the files downloaded. Can be local or absolute as long as the path is valid. Defaults to an empty string.

        Returns
        -------
        links: dict
            Contains dataframe objects for the `analysis_id`, given that the analysis has been complete.

        Examples
        -------
        >>> from core import SeerSDK
        >>> seer_sdk = SeerSDK()

        >>> seer_sdk.get_analysis_result("YOUR_ANALYSIS_ID_HERE")
        >>> {
                "peptide_np": <peptide_np dataframe object>,
                "peptide_panel": <peptide_panel dataframe object>,
                "protein_np": <protein_np dataframe object>,
                "protein_panel": <protein_panel dataframe object>
            }

        >>> seer_sdk.get_analysis_result("YOUR_ANALYSIS_ID_HERE", download_path="/Users/Downloads")
        >>> { "status": "Download complete." }
        """

        if not analysis_id:
            raise ValueError("Analysis ID cannot be empty.")

        if download_path and not os.path.exists(download_path):
            raise ValueError("The download path you entered is invalid.")

        if self.get_analysis(analysis_id)[0]["status"] in ["FAILED", None]:
            raise ValueError(
                "Cannot generate links for failed or null analyses."
            )

        ID_TOKEN, ACCESS_TOKEN = self._auth.get_token()
        HEADERS = {
            "Authorization": f"{ID_TOKEN}",
            "access-token": f"{ACCESS_TOKEN}",
        }
        URL = f"{self._auth.url}api/v1/data"

        with requests.Session() as s:
            s.headers.update(HEADERS)

            protein_data = s.get(
                f"{URL}/protein?analysisId={analysis_id}&retry=false"
            )

            if protein_data.status_code != 200:
                raise ValueError(
                    "Invalid request. Could not fetch protein data. Please check your parameters."
                )
            protein_data = protein_data.json()

            peptide_data = s.get(
                f"{URL}/peptide?analysisId={analysis_id}&retry=false"
            )

            if peptide_data.status_code != 200:
                raise ValueError(
                    "Invalid request. Could not fetch peptide data. Please check your parameters."
                )

            peptide_data = peptide_data.json()

            links = {
                "peptide_np": url_to_df(peptide_data["npLink"]["url"]),
                "peptide_panel": url_to_df(peptide_data["panelLink"]["url"]),
                "protein_np": url_to_df(protein_data["npLink"]["url"]),
                "protein_panel": url_to_df(protein_data["panelLink"]["url"]),
            }

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
        >>> from core import SeerSDK
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
        >>> from core import SeerSDK
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

        ID_TOKEN, ACCESS_TOKEN = self._auth.get_token()
        HEADERS = {
            "Authorization": f"{ID_TOKEN}",
            "access-token": f"{ACCESS_TOKEN}",
        }
        URL = (
            f"{self._auth.url}api/v1/msdataindex/filesinfolder?folder={folder}"
            if not space
            else f"{self._auth.url}api/v1/msdataindex/filesinfolder?folder={folder}&userGroupId={space}"
        )
        with requests.Session() as s:
            s.headers.update(HEADERS)

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

        ID_TOKEN, ACCESS_TOKEN = self._auth.get_token()
        HEADERS = {
            "Authorization": f"{ID_TOKEN}",
            "access-token": f"{ACCESS_TOKEN}",
        }
        URL = f"{self._auth.url}api/v1/msdataindex/download/getUrl"
        tenant_id = jwt.decode(ID_TOKEN, options={"verify_signature": False})[
            "custom:tenantId"
        ]

        for path in paths:
            with requests.Session() as s:
                s.headers.update(HEADERS)

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

    def group_analysis_results(self, analysis_id: str, box_plot: dict = None):
        """
        Returns the group analysis data for the given analysis id, provided it exists.

        Parameters
        ----------
        analysis_id : str
            The analysis id.

        box_plot : dict, optional
            The box plot configuration needed for the analysis, defaulted to None. Contains `feature_type` ("protein" or "peptide") and `feature_ids` (comma separated list of feature IDs) keys.

        Returns
        -------
        res : dict
            A dictionary containing the group analysis data.

        Examples
        -------
        >>> from core import SeerSDK
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

        ID_TOKEN, ACCESS_TOKEN = self._auth.get_token()
        HEADERS = {
            "Authorization": f"{ID_TOKEN}",
            "access-token": f"{ACCESS_TOKEN}",
        }
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
            "box_plot": [],
        }

        # Pre-GA data call
        with requests.Session() as s:
            s.headers.update(HEADERS)

            protein_pre_data = s.post(
                url=f"{URL}api/v2/groupanalysis/protein",
                json={"analysisId": analysis_id, "grouping": "condition"},
            )
            if protein_pre_data.status_code != 200:
                raise ValueError(
                    "Invalid request. Could not fetch group analysis protein pre data. Please check your parameters."
                )

            protein_pre_data = protein_pre_data.json()

            res["pre"]["protein"] = protein_pre_data

        with requests.Session() as s:
            s.headers.update(HEADERS)

            peptide_pre_data = s.post(
                url=f"{URL}api/v2/groupanalysis/peptide",
                json={"analysisId": analysis_id, "grouping": "condition"},
            )
            if peptide_pre_data.status_code != 200:
                raise ValueError(
                    "Invalid request. Could not fetch group analysis peptide pre data. Please check your parameters."
                )

            peptide_pre_data = peptide_pre_data.json()
            res["pre"]["peptide"] = peptide_pre_data

        # Post-GA data call
        with requests.Session() as s:
            s.headers.update(HEADERS)

            get_saved_result = s.get(
                f"{URL}api/v1/groupanalysis/getSavedResults?analysisid={analysis_id}"
            )

            if get_saved_result.status_code != 200:
                raise ValueError(
                    "Invalid request. Could not fetch group analysis post data. Please check your parameters."
                )
            get_saved_result = get_saved_result.json()

            # Protein data
            if "pgResult" in get_saved_result:
                res["post"]["protein"] = get_saved_result["pgResult"]

            # Peptide data
            if "peptideResult" in get_saved_result:
                res["post"]["peptide"] = get_saved_result["peptideResult"]

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

        # Box plot data call
        if not box_plot:
            del res["box_plot"]
            return res

        with requests.Session() as s:
            s.headers.update(HEADERS)
            box_plot["feature_type"] = box_plot["feature_type"].lower()
            box_plot_data = s.post(
                url=f"{URL}api/v1/groupanalysis/rawdata",
                json={
                    "analysisId": analysis_id,
                    "featureIds": (
                        ",".join(box_plot["feature_ids"])
                        if len(box_plot["feature_ids"]) > 1
                        else box_plot["feature_ids"][0]
                    ),
                    "featureType": f"{box_plot['feature_type']}group",
                },
            )
            if box_plot_data.status_code != 200:
                raise ValueError(
                    "Invalid request, could not fetch box plot data. Please verify your 'box_plot' parameters, including 'feature_ids' (comma-separated list of feature IDs) and 'feature_type' (needs to be a either 'protein' or 'peptide')."
                )

            box_plot_data = box_plot_data.json()
            res["box_plot"] = box_plot_data

        return res
