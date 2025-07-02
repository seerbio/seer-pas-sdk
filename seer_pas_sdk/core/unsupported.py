"""
seer_pas_sdk.core.unsupported -- in development
"""

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

from .sdk import SeerSDK as _SeerSDK


class _UnsupportedSDK(_SeerSDK):
    """
    **************
    [UNEXPOSED MODULE]
    **************

    This module is currently not supported and should be considered unstable. Use at your own risk.
    """

    def _add_sample(self, sample_entry: dict):
        """
        ****************
        [UNEXPOSED METHOD CALL]
        ****************
        Add a sample given a plate_id, sample_id, sample_name and space.

        Parameters
        ----------
        sample_entry: dict
            A dictionary containing all keys and values for the sample entry. These may or may not have been inferred from the sample description file.

        Returns
        -------
        dict
            The response from the backend.

        Examples
        -------
        >>> from core import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk._add_sample("YOUR_PLATE_ID_HERE", "YOUR_SAMPLE_ID_HERE", "YOUR_SAMPLE_NAME_HERE")
        >>> {
                "id": "SAMPLE_ID_HERE",
                "tenant_id": "TENANT_ID_HERE",
                "plate_id": "PLATE_ID_HERE",
                "sample_name": "SAMPLE_NAME_HERE",
                "sample_type": "SAMPLE_TYPE_HERE",
                "species": "Human",
                "description": None,
                ...
                ...
            }
        """
        for key in ["plateID", "sampleID", "sampleName"]:
            if key not in sample_entry:
                raise ValueError(
                    f"{key} is missing. Please check your parameters again."
                )

        URL = f"{self._auth.url}api/v1/samples"

        with self._get_auth_session() as s:

            response = s.post(URL, json=sample_entry)

            if response.status_code != 200:
                raise ValueError(
                    "Invalid request. Please check your parameters."
                )

            return response.json()

    # Add samples in batch
    def _add_samples(self, sample_info: list):
        """
        ****************
        [UNEXPOSED METHOD CALL]
        ****************
        Add samples in batch given a list of sample entries.

        Parameters:
        -----------
        sample_info: list
            A list of dictionaries containing all keys and values for the sample entries. These may or may not have been inferred from the sample description file.
            Required keys: ["plateID", "sampleID", "sampleName"]

        Returns:
        --------
        dict
            The response from the backend.
        """
        # Validate keys in samples
        for sample in sample_info:
            if not all(
                key in sample for key in ["plateID", "sampleID", "sampleName"]
            ):
                raise ValueError(
                    f"Invalid sample entry for sample {sample}. Please check your parameters again."
                )

        URL = f"{self._auth.url}api/v1/samples/batch"

        with self._get_auth_session() as s:
            response = s.post(URL, json={"samples": sample_info})

            if response.status_code != 200:
                raise ValueError(
                    "Invalid request. Please check your parameters."
                )

            return response.json()

    def add_project(
        self,
        project_name: str,
        plate_ids: _List[str],
        description: str = None,
        notes: str = None,
        space: str = None,
    ):
        """
        Creates a new project with a given project_name and a project_ids list.

        Parameters
        ----------
        project_name : str
            Name of the project.
        plate_ids : list[str]
            List of plate ids to be added to the project.
        description : str, optional
            Description of the project.
        notes : str, optional
            Notes for the project.
        space : str, optional
            User group id of the project. Defaults to the user group id of the user who is creating the project (i.e null).

        Returns
        -------
        res: dict
            A dictionary containing the status of the request if succeeded.

        Examples
        -------
        >>> from core import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.add_project("YOUR_PROJECT_NAME_HERE", ["PLATE_ID_1, PLATE_ID_2"])
        >>> {
                "status": "Project with id = PROJECT_ID started."
            }
        """

        if not project_name:
            raise ValueError("Project name cannot be empty.")

        all_plate_ids = set(
            [plate["id"] for plate in self.get_plate_metadata()]
        )

        for plate_id in plate_ids:
            if plate_id not in all_plate_ids:
                raise ValueError(
                    f"Plate ID '{plate_id}' is not valid. Please check your parameters again."
                )

        URL = f"{self._auth.url}api/v1/projects"

        with self._get_auth_session() as s:

            project = s.post(
                URL,
                json={
                    "projectName": project_name,
                    "plateIDs": plate_ids,
                    "notes": notes,
                    "description": description,
                    "projectUserGroup": space,
                },
            )

            if project.status_code != 200:
                raise ValueError(
                    "Invalid request. Please check your parameters."
                )

            res = {
                "status": f"Project started with id = {project.json()['id']}"
            }

            return res

    def add_samples_to_project(self, samples: _List[str], project_id: str):
        """
        Add samples to a project given a list of sample ids and a project id.

        Parameters
        ----------
        samples : list[str]
            List of sample ids to be added to the project.
        project_id : str
            ID of the project to which the samples are to be added.

        Returns
        -------
        res : dict
            A dictionary containing the status of the request if succeeded.

        Examples
        -------
        >>> from core import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.add_samples_to_project(["SAMPLE_ID_1", "SAMPLE_ID_2"], "PROJECT_ID")
        >>> {
                "status": "Samples added to PROJECT_ID"
            }
        """
        if not project_id:
            raise ValueError("Project ID cannot be empty.")

        if not samples:
            raise ValueError("Samples cannot be empty.")

        URL = f"{self._auth.url}api/v1/addSamplesToProject/{project_id}"

        with self._get_auth_session() as s:

            response = s.put(
                URL,
                json={
                    "sampleIDs": samples,
                },
            )

            if response.status_code != 200:
                raise ValueError(
                    "Invalid request. Please check your parameters."
                )

            res = {"status": f"Samples added to {project_id}"}
            return res

    def add_plates_to_project(self, plates: _List[str], project_id: str):
        """
        Add plates to a project given a list of plate ids and a project id.

        Parameters
        ----------
        plates : list[str]
            List of plate ids to be added to the project.
        project_id : str
            ID of the project to which the plates are to be added.

        Returns
        -------
        res : dict
            A dictionary containing the status of the request if succeeded.
        """

        if not project_id:
            raise ValueError("Project ID cannot be empty.")

        if not plates:
            raise ValueError("Plates cannot be empty.")

        # get samples
        samples = (
            x["id"]
            for plate_id in plates
            for x in self.get_samples(plate_id=plate_id)
        )

        return self.add_samples_to_project(
            project_id=project_id, samples=list(samples)
        )

    def add_plate(
        self,
        ms_data_files: _List[str],
        plate_map_file: str,
        plate_id: str,
        plate_name: str,
        sample_description_file: str = None,
        space: str = None,
    ):
        """
                Add a plate given a list of (existing or new) ms_data_files, plate_map_file, plate_id, plate_name, sample_description_file and space.

                Parameters
                ----------
                ms_data_files : list[str]
                    List of ms_data_files.
                plate_map_file : str or `PlateMap` Object
                    The plate map file.
                plate_id : str
                    The plate ID. Must be unique.
                plate_name : str
                    The plate name.
                sample_description_file : str, optional
                    The sample description file. Defaults to None.
                space : str, optional
                    The space or usergroup. Defaults to the user group id of the user who is creating the plate (i.e None).

                Returns
                -------
                id_uuid : str
        -            The UUID of the plate.

                Examples
                -------
                >>> from core import SeerSDK
                >>> seer_sdk = SeerSDK()
                >>> seer_sdk.add_plate(["MS_DATA_FILE_1", "MS_DATA_FILE_2"], "PLATE_MAP_FILE", "PLATE_ID", "PLATE_NAME")
                "9d5b6ab0-5a8c-11ef-8110-dd5cb94025eb"
        """

        plate_ids = (
            set()
        )  # contains all the plate_ids fetched from self.get_plate_metadata()
        files = []  # to be uploaded to sync frontend
        samples = []  # list of all the sample responses from the backend
        id_uuid = ""  # uuid for the plate id
        raw_file_paths = {}  # list of all the AWS raw file paths
        s3_upload_path = None
        s3_bucket = ""
        dir_exists = (
            True  # flag to check if the generated_files directory exists
        )

        # Step 0: Check if the file paths are valid.
        for file in ms_data_files:
            if not os.path.exists(file):
                raise ValueError(
                    f"File path '{file}' is invalid. Please check your parameters."
                )

        if type(plate_map_file) == str and not os.path.exists(plate_map_file):
            raise ValueError(
                f"File path '{plate_map_file}' is invalid. Please check your parameters."
            )

        if sample_description_file and not os.path.exists(
            sample_description_file
        ):
            raise ValueError(
                f"File path '{sample_description_file}' is invalid. Please check your parameters."
            )

        # Validate plate id, plate name as entity names
        # Enforcing this on the SDK level to prevent the creation of empty records before the backend validation
        if not entity_name_ruler(plate_id):
            raise ValueError("Plate ID contains unsupported characters.")

        if not entity_name_ruler(plate_name):
            raise ValueError("Plate Name contains unsupported characters.")

        # Validate plate map
        if isinstance(plate_map_file, PlateMap):
            plate_map_data = plate_map_file.to_df()
        else:
            plate_map_data = pd.read_csv(plate_map_file)

        local_file_names = [os.path.basename(x) for x in ms_data_files]

        validate_plate_map(plate_map_data, local_file_names)

        # Step 1: Check for duplicates in the user-inputted plate id. Populates `plate_ids` set.
        with self._get_auth_session() as s:
            plate_response = s.get(f"{self._auth.url}api/v1/plateids")

            if plate_response.status_code != 200:
                raise ValueError(
                    "Failed to fetch plate ids from the server. Please check your connection and reauthenticate."
                )

            plate_ids = set(plate_response.json()["data"])

            if not plate_ids:
                raise ValueError(
                    "No plate ids returned from the server. Please reattempt."
                )

        # Step 2: Fetch the UUID that needs to be passed into the backend from `/api/v1/plates` to fetch the AWS upload config and raw file path. This will sync the plates backend with samples when the user uploads later. This UUID will also be void of duplicates since duplication is handled by the backend.

        with self._get_auth_session() as s:
            plate_response = s.post(
                f"{self._auth.url}api/v1/plates",
                json={
                    "plateId": plate_id,
                    "plateName": plate_name,
                    "plateUserGroup": space,
                },
            )

            if plate_response.status_code != 200:
                raise ValueError(
                    "Failed to connect to the server. Please check your connection and reauthenticate."
                )

            id_uuid = plate_response.json()["id"]

            if not id_uuid:
                raise ValueError(
                    "Failed to fetch a UUID from the server. Please check your connection and reauthenticate."
                )

        # Step 3: Fetch AWS upload config from the backend with the plateId we just generated. Populates `s3_upload_path` and `s3_bucket` global variables.
        with self._get_auth_session() as s:
            config_response = s.post(
                f"{self._auth.url}api/v1/msdatas/getuploadconfig",
                json={"plateId": id_uuid},
            )

            if (
                config_response.status_code != 200
                or not config_response.json()
            ):
                raise ValueError(
                    "Failed to fetch AWS upload config for the plate. Please check your connection and reauthenticate."
                )

            if "s3Bucket" not in config_response.json():
                raise ValueError(
                    "Failed to fetch the S3 bucket from AWS. Please check your connection and reauthenticate."
                )
            elif "s3UploadPath" not in config_response.json():
                raise ValueError(
                    "Failed to fetch the S3 upload path from AWS. Please check your connection and reauthenticate."
                )

            s3_bucket = config_response.json()["s3Bucket"]
            s3_upload_path = config_response.json()["s3UploadPath"]

        with self._get_auth_session() as s:
            config_response = s.get(
                f"{self._auth.url}auth/getawscredential",
            )

            if (
                config_response.status_code != 200
                or not config_response.json()
            ):
                raise ValueError(
                    "Failed to fetch credentials. Please check your connection and reauthenticate."
                )

            if "S3Bucket" not in config_response.json()["credentials"]:
                raise ValueError(
                    "Failed to fetch data from AWS. Please check your connection and reauthenticate."
                )

            credentials = config_response.json()["credentials"]

        # Step 4: Upload the platemap file to the S3 bucket.
        if isinstance(plate_map_file, PlateMap):
            plate_map_file_name = f"plateMap_{id_uuid}.csv"

            if not os.path.exists("generated_files"):
                dir_exists = False
                os.makedirs("generated_files")

            plate_map_file.to_csv(f"generated_files/{plate_map_file_name}")
            plate_map_file = f"generated_files/{plate_map_file_name}"

        else:
            plate_map_file_name = os.path.basename(plate_map_file)

        res = upload_file(
            plate_map_file,
            s3_bucket,
            credentials,
            f"{s3_upload_path}{plate_map_file_name}",
        )

        if not res:
            raise ValueError(
                "Failed to upload plate map to AWS. Please check your connection and reauthenticate."
            )

        with self._get_auth_session() as s:
            plate_map_response = s.post(
                f"{self._auth.url}api/v1/msdataindex/file",
                json={
                    "files": [
                        {
                            "filePath": f"{s3_upload_path}{plate_map_file_name}",
                            "fileSize": os.stat(plate_map_file).st_size,
                            "userGroupId": space,
                        }
                    ]
                },
            )

            if (
                plate_map_response.status_code != 200
                or not plate_map_response.json()
                or "created" not in plate_map_response.json()
            ):
                raise ValueError(
                    "Failed to upload raw files to PAS. Please check your connection and reauthenticate."
                )

        # Step 5: Populate `raw_file_paths` for sample upload.
        for file in ms_data_files:
            filename = os.path.basename(file)
            filesize = os.stat(file).st_size
            raw_file_paths[f"{filename}"] = (
                f"/{s3_bucket}/{s3_upload_path}{filename}"
            )

        sample_info = get_sample_info(
            id_uuid,
            plate_map_file,
            space,
            sample_description_file,
        )

        # Step 6: Get sample info from the plate map file and make a call to `/api/v1/samples` with the sample_info. This returns the plateId, sampleId and sampleName for each sample in the plate map file. Also validate and upload the sample_description_file if it exists.
        if sample_description_file:

            sdf_upload = upload_file(
                sample_description_file,
                s3_bucket,
                credentials,
                f"{s3_upload_path}{os.path.basename(sample_description_file)}",
            )

            if not sdf_upload:
                raise ValueError(
                    "Failed to upload sample description file to AWS. Please check your connection and reauthenticate."
                )

            with self._get_auth_session() as s:
                sdf_response = s.post(
                    f"{self._auth.url}api/v1/msdataindex/file",
                    json={
                        "files": [
                            {
                                "filePath": f"{s3_upload_path}{os.path.basename(sample_description_file)}",
                                "fileSize": os.stat(
                                    sample_description_file
                                ).st_size,
                                "userGroupId": space,
                            }
                        ]
                    },
                )

                if (
                    sdf_response.status_code != 200
                    or not sdf_response.json()
                    or "created" not in sdf_response.json()
                ):
                    raise ValueError(
                        "Failed to upload sample description file to PAS DB. Please check your connection and reauthenticate."
                    )

        samples = self._add_samples(sample_info)

        # Step 7: Parse the plate map file and convert the data into a form that can be POSTed to `/api/v1/msdatas`.
        plate_map_data = parse_plate_map_file(
            plate_map_file, samples, raw_file_paths, space
        )

        # Step 8: Make a request to `/api/v1/msdatas/batch` with the processed samples data.
        with self._get_auth_session() as s:
            ms_data_response = s.post(
                f"{self._auth.url}api/v1/msdatas/batch",
                json={"msdatas": plate_map_data},
            )
            if ms_data_response.status_code != 200:
                raise ValueError(
                    "Failed to create samples in PAS. Please check your connection and reauthenticate."
                )

        # Step 9: Upload each msdata file to the S3 bucket.
        with self._get_auth_session() as s:
            config_response = s.get(
                f"{self._auth.url}auth/getawscredential",
            )

            if (
                config_response.status_code != 200
                or not config_response.json()
            ):
                raise ValueError("Could not fetch config for user.")

            if "S3Bucket" not in config_response.json()["credentials"]:
                raise ValueError(
                    "Failed to connect to AWS. Please check your connection and reauthenticate."
                )

            credentials = config_response.json()["credentials"]

            os.environ["AWS_ACCESS_KEY_ID"] = credentials["AccessKeyId"]
            os.environ["AWS_SECRET_ACCESS_KEY"] = credentials[
                "SecretAccessKey"
            ]
            os.environ["AWS_SESSION_TOKEN"] = credentials["SessionToken"]

        for file in ms_data_files:
            filename = os.path.basename(file)
            filesize = os.stat(file).st_size
            res = upload_file(
                file, s3_bucket, credentials, f"{s3_upload_path}{filename}"
            )

            if not res:
                raise ValueError(
                    "Failed to upload MS data files to AWS. Please check your connection and reauthenticate."
                )

            files.append(
                {
                    "filePath": f"{s3_upload_path}{filename}",
                    "fileSize": filesize,
                    "userGroupId": space,
                }
            )

        # Step 10: Make a call to `api/v1/msdataindex/file` to sync with frontend. This should only be done after all files have finished uploading, simulating an async "promise"-like scenario in JavaScript.
        with self._get_auth_session() as s:
            file_response = s.post(
                f"{self._auth.url}api/v1/msdataindex/file",
                json={"files": files},
            )

            if (
                file_response.status_code != 200
                or not file_response.json()
                or "created" not in file_response.json()
            ):
                raise ValueError(
                    "Failed to update PAS MS Files view. Your data has been uploaded."
                )

        if os.path.exists("generated_files") and not dir_exists:
            shutil.rmtree("generated_files")

        print(f"Plate generated with id: '{id_uuid}'")
        return id_uuid

    def start_analysis(
        self,
        name: str,
        project_id: str,
        sample_ids: list = None,
        analysis_protocol_name: str = None,
        analysis_protocol_id: str = None,
        notes: str = "",
        description: str = "",
        space: str = None,
        filter: str = None,
    ):
        """
        Given a name, analysis_protocol_id, project_id, creates a new analysis for the authenticated user.

        Parameters
        ----------
        name : str
            Name of the analysis.

        project_id : str
            ID of the project to which the analysis belongs. Can be fetched using the get_project_metadata() function.

        sample_ids: list[str], optional
            List of sample IDs to be used for the analysis. Should be omitted if analysis is to be run with all samples.

        analysis_protocol_name : str, optional
            Name of the analysis protocol to be used for the analysis. Can be fetched using the get_analysis_protocols() function. Should be omitted if analysis_protocol_id is provided.

        analysis_protocol_id : str, optional
            ID of the analysis protocol to be used for the analysis. Can be fetched using the get_analysis_protocols() function. Should be omitted if analysis_protocol_name is provided.

        notes : str, optional
            Notes for the analysis, defaulted to an empty string.

        description : str, optional
            Description for the analysis, defaulted to an empty string.

        space : str, optional
            ID of the user group to which the analysis belongs, defaulted to None.

        filter : str, optional
            Filter to be applied to the samples, defaulted to None. Acceptable values are 'sample', 'control', or None.

        Returns
        -------
        dict
            Contains message whether the analysis was started or not.

        Examples
        -------
        >>> from core import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.start_analysis("YOUR_ANALYSIS_NAME_HERE", "YOUR_PROJECT_ID_HERE", "YOUR_ANALYSIS_PROTOCOL_ID_HERE")
        >>> { "message": "Analysis has been started successfully" }
        """

        if not name:
            raise ValueError("Analysis name cannot be empty.")

        if not project_id:
            raise ValueError("Project ID cannot be empty.")

        if not analysis_protocol_id and analysis_protocol_name:
            valid_analysis_protocol = self.get_analysis_protocols(
                analysis_protocol_name=analysis_protocol_name
            )

            if not valid_analysis_protocol:
                raise ValueError(
                    f"Analysis protocol not found with name {analysis_protocol_name}."
                )

            analysis_protocol_id = valid_analysis_protocol[0]["id"]

        if analysis_protocol_id and not analysis_protocol_name:
            valid_analysis_protocol = self.get_analysis_protocols(
                analysis_protocol_id=analysis_protocol_id
            )

            if not valid_analysis_protocol:
                raise ValueError(
                    f"Analysis protocol not found with ID {analysis_protocol_id}."
                )

        if not analysis_protocol_id and not analysis_protocol_name:
            raise ValueError(
                "You must specify either analysis protocol ID or analysis protocol name."
            )

        if sample_ids:
            valid_ids = [
                entry["id"]
                for entry in self.get_samples(project_id=project_id)
            ]

            for sample_id in sample_ids:
                if sample_id not in valid_ids:
                    raise ValueError(
                        f"Sample ID '{sample_id}' is either not valid or not associated with the project."
                    )
        if filter:
            sample_ids = self._filter_samples_metadata(
                project_id, filter, sample_ids
            )

        URL = f"{self._auth.url}api/v1/analyze"

        with self._get_auth_session() as s:
            req_payload = {
                "analysisName": name,
                "analysisProtocolId": analysis_protocol_id,
                "projectId": project_id,
                "notes": notes,
                "description": description,
                "userGroupId": space,
            }

            if sample_ids:
                sample_ids = ",".join(sample_ids)
                req_payload["selectedSampleIDs"] = sample_ids

            analysis = s.post(URL, json=req_payload)

            if analysis.status_code != 200:
                raise ValueError(
                    "Failed to start analysis. Please check your connection."
                )

            # Analysis id is not contained in response.
            return analysis.json()

    def upload_ms_data_files(
        self,
        ms_data_files: list,
        path: str,
        space: str = None,
        filenames=[],
    ):
        """
        Upload MS data files to the backend.

        Parameters
        ----------
        ms_data_files : List
            List of MS data files to be uploaded.
        path : str
            The name of the destination folder in PAS. Does not accept leading, trailing or consecutive forward slashes. Example: "path/to/pas/folder".
        space: str, optional
            ID of the user group to which the files belongs, defaulted to None.
        filenames: list, optional
            List of preferred PAS filenames. This rename occurs on both the cloud and the user interface level. Indexes should be mapped to the correlating source file in ms_data_files. Folder paths are not accepted. Defaulted to [].

        Returns
        -------
        dict
            Contains message whether the files were uploaded or not.

        Examples
        -------
        >>> from core import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.upload_ms_data_files(["/path/to/file1", "/path/to/file2"])
            [{'filePath': '/path/to/file1', 'fileSize': 1234, 'userGroupId': None}, {'filePath': '/path/to/file2', 'fileSize': 1234, 'userGroupId': None}]

        >>> seer_sdk.upload_ms_data_files(["/path/to/file1", "/path/to/file2"], path="path/to/pas/folder")
            [{'filePath': 'path/to/pas/folder/file1', 'fileSize': 1234, 'userGroupId': None}, {'filePath': 'path/to/pas/folder/file2', 'fileSize': 1234, 'userGroupId': None}]

        >>> seer_sdk.upload_ms_data_files(["/path/to/file1", "/path/to/file2"], path="path/to/pas/folder", space="user_group_id")
            [{'filePath': 'path/to/pas/folder/file1', 'fileSize': 1234, 'userGroupId': 'user_group_id'}, {'filePath': 'path/to/pas/folder/file2', 'fileSize': 1234, 'userGroupId': 'user_group_id'}]

        >>> seer_sdk.upload_ms_data_files(["/path/to/file1", "/path/to/file2"], path="path/to/pas/folder", space="user_group_id", filenames=["fileA", "fileB"])
            [{'filePath': 'path/to/pas/folder/fileA', 'fileSize': 1234, 'userGroupId': 'user_group_id'}, {'filePath': 'path/to/pas/folder/fileB', 'fileSize': 1234, 'userGroupId': 'user_group_id'}]

        """

        files = []
        tenant_id = self._auth.active_tenant_id
        s3_bucket = ""

        if not path:
            raise ValueError(
                "A folder path is required to upload files into PAS."
            )

        # Step 1: Check if paths and file extensions are valid.
        for file in ms_data_files:
            if not valid_ms_data_file(file):
                raise ValueError(
                    "Invalid file or file format. Please check your file."
                )

        extensions = set(
            [os.path.splitext(file.lower())[1] for file in ms_data_files]
        )

        if filenames and ".d.zip" in extensions:
            raise ValueError(
                "Please leave the 'filenames' parameter empty when working with .d.zip files. SeerSDK.rename_d_zip_file() is available for this use case."
            )
        # Step 2: Use active tenant to fetch the tenant_id.
        tenant_id = self.get_active_tenant_id()

        # Step 3: Fetch the S3 bucket name by making a call to `/api/v1/auth/getawscredential`
        with self._get_auth_session() as s:
            config_response = s.get(
                f"{self._auth.url}auth/getawscredential",
            )

            if (
                config_response.status_code != 200
                or not config_response.json()
            ):
                raise ValueError("Could not fetch config for user.")

            if "S3Bucket" not in config_response.json()["credentials"]:
                raise ValueError(
                    "Could not fetch config for user - incomplete response."
                )

            s3_bucket = config_response.json()["credentials"]["S3Bucket"]

            credentials = config_response.json()["credentials"]

        # Step 4: Upload each msdata file to the S3 bucket.
        for i, file in enumerate(ms_data_files):
            filename = (
                filenames[i]
                if filenames
                else os.path.basename(file).replace("/", "")
            )
            filesize = os.stat(file).st_size
            s3_upload_path = (
                f"{tenant_id}" if not path else f"{tenant_id}/{path}"
            )

            res = upload_file(
                file, s3_bucket, credentials, f"{s3_upload_path}/{filename}"
            )

            if not res:
                raise ServerError(
                    f"Failed to upload to cloud storage. {filename}"
                )

            files.append(
                {
                    "filePath": f"{s3_upload_path}/{filename}",
                    "fileSize": filesize,
                    "userGroupId": space,
                }
            )

        # Step 5: Make a call to `/api/v1/msdataindex/file` to sync with frontend. This should only be done after all files have finished uploading, simulating an async "promise"-like scenario in JavaScript.
        result_files = None
        with self._get_auth_session() as s:
            file_response = s.post(
                f"{self._auth.url}api/v1/msdataindex/file",
                json={"files": files},
            )

            if (
                file_response.status_code != 200
                or not file_response.json()
                or "created" not in file_response.json()
            ):
                raise ServerError("Could not upload MS Files to PAS.")
            result_files = file_response.json()["files"]

        # omit tenant_id from return file path
        for result in result_files:
            result["filePath"] = "/".join(result["filePath"].split("/")[1:])

        print(
            f"Files uploaded successfully to {self.get_active_tenant_name()}."
        )

        return result_files

    def _move_ms_data_files(
        self,
        source_data_files: _List,
        target_data_files: _List,
        target_space: str = None,
    ):
        """
        Move MS data files from one location to another.

        Parameters
        ----------
        source_data_files : List
            List of MS data files to be moved.
        target_data_files : List
            List of target MS data files.
        target_space : str, optional
            Name of the user group to move the files to.
            If None is provided, the files will remain in the same space prior to the move action.

        Returns
        -------
        list
            The list of files moved.

        Examples
        -------
        >>> from core import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.move_ms_data_files(["/path/to/file1", "/path/to/file2"], ["/path/to/target_file1", "/path/to/target_file2"])
        ["/path/to/target_file1", "/path/to/target_file2"]
        """

        tenant_id = self._auth.active_tenant_id

        if not source_data_files:
            raise ValueError("Source data files cannot be empty.")

        if len(source_data_files) != len(target_data_files):
            raise ValueError(
                "Source and target files should have the same number of files."
            )

        folder_paths = list({os.path.dirname(x) for x in source_data_files})
        if len(folder_paths) > 1:
            raise ValueError(
                "Files can only be moved from one folder path at a time."
            )
        folder_path = f"{tenant_id}/{folder_paths[0]}"

        target_folder_paths = list(
            {os.path.dirname(x) for x in target_data_files}
        )
        if len(target_folder_paths) > 1:
            raise ValueError(
                "Files can only be moved to one folder path at a time."
            )

        available_spaces = self.get_spaces()
        target_space_id = None
        if target_space:
            target_spaces = [
                x["id"]
                for x in available_spaces
                if x["usergroup_name"].lower() == target_space.lower()
            ]
            if not target_spaces:
                raise ValueError(
                    f"Target space not found with name {target_space}. Please correct this value."
                )
            target_space_id = target_spaces[0]

        target_folder_path = f"{tenant_id}/{target_folder_paths[0]}"
        # Retrieve msdatafileindex metadata to determine source space
        base_space = None
        with self._get_auth_session() as s:
            URL = self._auth.url + "api/v1/msdataindex/getmetadata"
            params = {"folderKey": folder_path}
            r = s.get(URL, params=params)
            if r.status_code != 200:
                raise ValueError("Failed to locate source files in PAS.")
            data = r.json()["files"]
            found_files = [
                x
                for x in data
                if x["filename"]
                in [os.path.basename(x) for x in source_data_files]
            ]
            if len(found_files) != len(source_data_files):
                raise ValueError(
                    "Not all source files were found in the source folder."
                )
            spaces = list({x["userGroupId"] for x in found_files})
            if len(spaces) > 1:
                raise ValueError(
                    "Files are located in multiple spaces. Please separate these into multiple move requests."
                )
            base_space = spaces[0]

        if not target_space:
            target_space_id = base_space

        json = {
            "type": "file",
            "sourceFolder": folder_path,
            "targetFolder": target_folder_path,
            "sourceFiles": [os.path.basename(x) for x in source_data_files],
            "targetFiles": [os.path.basename(x) for x in target_data_files],
        }

        # we must specify base_space if not General because it's a criteria for finding source files.
        if base_space:
            json["sourceUserGroupId"] = base_space

        # If target space is General, we still omit it
        if target_space_id and base_space != target_space_id:
            json["targetUserGroupId"] = target_space_id

        with self._get_auth_session() as s:
            URL = self._auth.url + "api/v1/msdataindex/move"
            json = json
            r = s.post(URL, json=json)
            if r.status_code != 200:
                raise ServerError("Failed to move files in PAS.")
            return target_data_files

    def change_ms_file_space(
        self, ms_data_files: _List, destination_space: str
    ):
        """
        Change the space of MS data files.

        Parameters
        ----------
        ms_data_files : List
            List of MS data files to be moved.
        destination_space : str
            name of the desired user group

        Returns
        -------
        List
            List of files that were converted to the new space.
        """
        return self._move_ms_data_files(
            ms_data_files, ms_data_files, destination_space
        )

    def move_ms_data_files(
        self, source_ms_data_files: _List, target_ms_data_files: _List
    ):
        """
        Move MS data files from one PAS file location to another. Space will be unchanged.

        Parameters
        ----------
        source_ms_data_files : List
            List of file paths of the MS data files to be moved.
        target_ms_data_files : List
            List of destination file paths. Should be indexed one to one with the source ms data files list.

        Returns
        -------
            List
                List of files that were moved.
        """
        return self._move_ms_data_files(
            source_ms_data_files, target_ms_data_files
        )

    def download_analysis_files(
        self, analysis_id: str, download_path: str = "", file_name: str = ""
    ):
        """
        Download a specific analysis file from the backend given an `analysis_id` to the specified `download_path`.

        If no `download_path` is specified, the file will be downloaded to the current working directory.

        If no `file_name` is specified, all files for the analysis will be downloaded.

        Parameters
        ----------
        analysis_id : str
            ID of the analysis to download.
        download_path : str, optional
            Path to download the analysis file to, defaulted to current working directory.
        file_name : str, optional
            Name of the analysis file to download, defaulted to None.

        Returns
        -------
        dict
            Message containing whether the file was downloaded or not.

        Examples
        -------
        >>> from core import SeerSDK
        >>> sdk = SeerSDK()
        >>> sdk.download_analysis_files("analysis_id", "/path/to/download")
        >>> Downloading EXP22006_2022ms0031bX25_B_BA4_1_4768/diann.log
            Finished downloading EXP22006_2022ms0031bX25_B_BA4_1_4768/diann.log

            Downloading EXP20004_2020ms0007X11_A.mzML.quant
            Finished downloading EXP20004_2020ms0007X11_A.mzML.quant

            Downloading EXP20004_2020ms0007X11_A/0714-diann181-libfree-mbr.json
            Finished downloading EXP20004_2020ms0007X11_A/0714-diann181-libfree-mbr.json

            Downloading EXP20004_2020ms0007X11_A/diann.log
            Finished downloading EXP20004_2020ms0007X11_A/diann.log
        >>> { "message": "File downloaded successfully." }
        """

        def get_url(analysis_id, file_name, project_id):
            URL = f"{self._auth.url}api/v1/analysisResultFiles/getUrl"

            with self._get_auth_session() as s:

                download_url = s.post(
                    URL,
                    json={
                        "analysisId": analysis_id,
                        "filename": file_name,
                        "projectId": project_id,
                    },
                )

                if download_url.status_code != 200:
                    raise ValueError(
                        "Could not download file. Please check if the analysis ID is valid or the backend is running."
                    )

                return download_url.json()["url"]

        if not analysis_id:
            raise ValueError("Analysis ID cannot be empty.")

        try:
            valid_analysis = self.get_analyses(analysis_id)[0]
        except:
            raise ValueError(
                "Invalid analysis ID. Please check if the analysis ID is valid or the backend is running."
            )

        project_id = valid_analysis["project_id"]

        if not download_path:
            download_path = os.getcwd()
            print(f"\nDownload path not specified.\n")

        if not os.path.isdir(download_path):
            print(
                f'\nThe path "{download_path}" you specified does not exist, was either invalid or not absolute.\n'
            )
            download_path = os.getcwd()

        name = f"{download_path}/downloads/{analysis_id}"

        if not os.path.exists(name):
            os.makedirs(name)

        URL = f"{self._auth.url}api/v1/analysisResultFiles"

        with self._get_auth_session() as s:

            analysis_files = s.get(f"{URL}/{analysis_id}")

            if analysis_files.status_code != 200:
                raise ValueError(
                    "Invalid request. Please check if the analysis ID is valid or the backend is running."
                )

            res = analysis_files.json()

        if file_name:
            filenames = set([file["filename"] for file in res])

            if file_name not in filenames:
                raise ValueError(
                    "Invalid file name. Please check if the file name is correct."
                )

            res = [file for file in res if file["filename"] == file_name]

        print(f'Downloading files to "{name}"\n')

        for file in res:
            filename = file["filename"]
            url = get_url(analysis_id, filename, project_id)

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

        return {
            "message": f"Files downloaded successfully to '{download_path}/downloads/{analysis_id}'"
        }

    def link_plate(
        self,
        ms_data_files: _List[str],
        plate_map_file: str,
        plate_id: str,
        plate_name: str,
        sample_description_file: str = None,
        space: str = None,
    ):
        """
        Links existing MS data files to user uploaded files to create a new plate.

        Parameters
        ----------
        ms_data_files : list[str]
            Path to MS data files on the PAS backend or S3 bucket.
        plate_map_file : str
            Path to the plate map file to be linked.
        plate_id : str
            ID of the plate to be linked.
        plate_name : str
            Name of the plate to be linked.
        sample_description_file : str, optional
            Path to the sample description file to be linked, defaulted to None.
        space : str, optional
            ID of the user group to which the files belongs, defaulted to None.

        Returns
        -------
        dict
            Contains the message whether the plate was created or not.

        Examples
        -------
        >>> from core import SeerSDK
        >>> sdk = SeerSDK()
        >>> sdk.link_plate(["/path/to/file1", "/path/to/file2"], "/path/to/plate_map_file", "plate_id", "plate_name")
        >>> { "message": "Plate generated with id: 'plate_id'" }
        """

        plate_ids = (
            set()
        )  # contains all the plate_ids fetched from self.get_plate_metadata()
        files = []  # to be uploaded to sync frontend
        samples = []  # list of all the sample responses from the backend
        id_uuid = ""  # uuid for the plate id
        raw_file_paths = {}  # list of all the AWS raw file paths
        s3_upload_path = None
        s3_bucket = ""
        ms_data_file_names = []
        dir_exists = (
            True  # flag to check if the generated_files directory exists
        )

        # Step 0: Check if the file paths exist in the S3 bucket.
        for file in ms_data_files:
            if not self.list_ms_data_files(file):
                raise ValueError(
                    f"File '{file}' does not exist. Please check your parameters."
                )

        if sample_description_file and not os.path.exists(
            sample_description_file
        ):
            raise ValueError(
                f"File path '{sample_description_file}' is invalid. Please check your parameters."
            )

        # Validate plate id, plate name as entity names
        # Enforcing this on the SDK level to prevent the creation of empty records before the backend validation
        if not entity_name_ruler(plate_id):
            raise ValueError("Plate ID contains unsupported characters.")

        if not entity_name_ruler(plate_name):
            raise ValueError("Plate Name contains unsupported characters.")

        # Validate plate map
        if isinstance(plate_map_file, PlateMap):
            plate_map_data = plate_map_file.to_df()
        else:
            plate_map_data = pd.read_csv(plate_map_file)

        validate_plate_map(plate_map_data, ms_data_files)

        # Step 1: Check for duplicates in the user-inputted plate id. Populates `plate_ids` set.
        with self._get_auth_session() as s:
            plate_response = s.get(f"{self._auth.url}api/v1/plateids")

            if plate_response.status_code != 200:
                raise ServerError(
                    "Failed to fetch plate ids from the server. Please check your connection and reauthenticate."
                )

            plate_ids = set(plate_response.json()["data"])

            if not plate_ids:
                raise ServerError(
                    "No plate ids returned from the server. Please reattempt."
                )

        # Step 2: Fetch the UUID that needs to be passed into the backend from `/api/v1/plates` to fetch the AWS upload config and raw file path. This will sync the plates backend with samples when the user uploads later. This UUID will also be void of duplicates since duplication is handled by the backend.

        with self._get_auth_session() as s:
            plate_response = s.post(
                f"{self._auth.url}api/v1/plates",
                json={
                    "plateId": plate_id,
                    "plateName": plate_name,
                    "plateUserGroup": space,
                },
            )

            if plate_response.status_code != 200:
                raise ServerError(
                    "Failed to connect to the server. Please check your connection and reauthenticate."
                )

            id_uuid = plate_response.json()["id"]

            if not id_uuid:
                raise ServerError(
                    "Failed to fetch a UUID from the server. Please check your connection and reauthenticate."
                )

        # Step 3: Fetch AWS upload config from the backend with the plateId we just generated. Populates `s3_upload_path` and `s3_bucket` global variables.
        with self._get_auth_session() as s:
            config_response = s.post(
                f"{self._auth.url}api/v1/msdatas/getuploadconfig",
                json={"plateId": id_uuid},
            )

            if (
                config_response.status_code != 200
                or not config_response.json()
            ):
                raise ServerError(
                    "Failed to fetch AWS upload config for the plate. Please check your connection and reauthenticate."
                )

            if "s3Bucket" not in config_response.json():
                raise ServerError(
                    "Failed to fetch the S3 bucket from AWS. Please check your connection and reauthenticate."
                )
            elif "s3UploadPath" not in config_response.json():
                raise ServerError(
                    "Failed to fetch the S3 upload path from AWS. Please check your connection and reauthenticate."
                )

            s3_bucket = config_response.json()["s3Bucket"]
            s3_upload_path = config_response.json()["s3UploadPath"]

        with self._get_auth_session() as s:
            config_response = s.get(
                f"{self._auth.url}auth/getawscredential",
            )

            if (
                config_response.status_code != 200
                or not config_response.json()
            ):
                raise ServerError(
                    "Failed to fetch credentials. Please check your connection and reauthenticate."
                )

            if "S3Bucket" not in config_response.json()["credentials"]:
                raise ServerError(
                    "Failed to fetch data from AWS. Please check your connection and reauthenticate."
                )

            credentials = config_response.json()["credentials"]

        # Step 4: Upload the platemap file to the S3 bucket.
        if isinstance(plate_map_file, PlateMap):
            plate_map_file_name = f"plateMap_{id_uuid}.csv"

            if not os.path.exists("generated_files"):
                dir_exists = False
                os.makedirs("generated_files")

            plate_map_file.to_csv(f"generated_files/{plate_map_file_name}")
            plate_map_file = f"generated_files/{plate_map_file_name}"

        else:
            plate_map_file_name = os.path.basename(plate_map_file)

        res = upload_file(
            plate_map_file,
            s3_bucket,
            credentials,
            f"{s3_upload_path}{plate_map_file_name}",
        )

        if not res:
            raise ServerError(
                "Failed to upload plate map to AWS. Please check your connection and reauthenticate."
            )

        with self._get_auth_session() as s:
            plate_map_response = s.post(
                f"{self._auth.url}api/v1/msdataindex/file",
                json={
                    "files": [
                        {
                            "filePath": f"{s3_upload_path}{plate_map_file_name}",
                            "fileSize": os.stat(plate_map_file).st_size,
                            "userGroupId": space,
                        }
                    ]
                },
            )

            if (
                plate_map_response.status_code != 200
                or not plate_map_response.json()
                or "created" not in plate_map_response.json()
            ):
                raise ServerError(
                    "Failed to upload raw files to PAS. Please check your connection and reauthenticate."
                )

        # Step 5: Populate `raw_file_paths` for sample upload.
        raw_file_paths = self._get_msdataindex_path(ms_data_files)

        # Step 5.5: trim display paths to basename to align with plate map
        raw_file_paths = {
            os.path.basename(k): v for k, v in raw_file_paths.items()
        }

        # Step 6: Get sample info from the plate map file and make a call to `/api/v1/samples` with the sample_info. This returns the plateId, sampleId and sampleName for each sample in the plate map file. Also validate and upload the sample_description_file if it exists.
        sample_info = get_sample_info(
            id_uuid,
            plate_map_file,
            space,
            sample_description_file,
        )
        if sample_description_file:
            sdf_upload = upload_file(
                sample_description_file,
                s3_bucket,
                credentials,
                f"{s3_upload_path}{os.path.basename(sample_description_file)}",
            )

            if not sdf_upload:
                raise ValueError(
                    "Failed to upload sample description file to AWS. Please check your connection and reauthenticate."
                )

            with self._get_auth_session() as s:
                sdf_response = s.post(
                    f"{self._auth.url}api/v1/msdataindex/file",
                    json={
                        "files": [
                            {
                                "filePath": f"{s3_upload_path}{os.path.basename(sample_description_file)}",
                                "fileSize": os.stat(
                                    sample_description_file
                                ).st_size,
                                "userGroupId": space,
                            }
                        ]
                    },
                )

                if (
                    sdf_response.status_code != 200
                    or not sdf_response.json()
                    or "created" not in sdf_response.json()
                ):
                    raise ServerError(
                        "Failed to upload sample description file to PAS DB. Please check your connection and reauthenticate."
                    )

        for entry in sample_info:
            sample = self._add_sample(entry)
            samples.append(sample)

        # Step 7: Parse the plate map file and convert the data into a form that can be POSTed to `/api/v1/msdatas`.
        plate_map_data = parse_plate_map_file(
            plate_map_file, samples, raw_file_paths, space
        )

        # Step 8: Make a request to `/api/v1/msdatas/batch` with the processed samples data.
        with self._get_auth_session() as s:
            ms_data_response = s.post(
                f"{self._auth.url}api/v1/msdatas/batch",
                json={"msdatas": plate_map_data},
            )
            if ms_data_response.status_code != 200:
                raise ServerError(
                    "Failed to add samples to plate in PAS. Please check your connection and reauthenticate."
                )

        print(f"Plate generated with id: '{id_uuid}'")
        return id_uuid

    def _get_msdataindex_metadata(self, folder=""):
        """
        Get metadata for a given file path.

        Raises:
            ServerError - could not fetch metadata for file.

        Returns:
            dict: A dictionary containing the metadata for the file.
        """
        URL = f"{self._auth.url}api/v2/msdataindex/getmetadata"
        with self._get_auth_session() as s:
            params = {"all": "true"}
            if folder:
                tenant_id = jwt.decode(
                    self._auth.get_token()[0],
                    options={"verify_signature": False},
                )["custom:tenantId"]
                params["folderKey"] = f"{tenant_id}/{folder}"
                print(params["folderKey"])

            metadata = s.get(URL, params=params)

            if metadata.status_code != 200:
                print(metadata.text)
                raise ServerError("Could not fetch metadata for file.")

            return metadata.json()

    def _get_msdataindex_path(self, display_path: list):
        """
        Get the underlying cloud file path from the display path.

        Args:
            display_path (list): A list of file paths as displayed on PAS

        Returns:
            dict: A dictionary mapping the display path to the raw file path.
        """

        tenant_id = jwt.decode(
            self._auth.get_token()[0], options={"verify_signature": False}
        )["custom:tenantId"]
        result = {}
        # partition by folder_path
        folder_partitions = {os.path.dirname(x): [] for x in display_path}
        for path in display_path:
            folder_partitions[os.path.dirname(path)].append(path)

        success = True
        missing_data_files = []
        # For every unique folder in the set of MS files, fetch the metadata
        for folder_path in folder_partitions:
            try:
                metadata = {
                    x["key"]: x["rawFilePath"]
                    for x in self._get_msdataindex_metadata(
                        folder=folder_path
                    )["data"]
                }
            except:
                # If the metadata fetch fails, skip the folder
                continue

            for display_path in folder_partitions[folder_path]:
                if f"{tenant_id}/{display_path}" not in metadata:
                    if success:
                        success = False
                    missing_data_files.append(display_path)
                result[display_path] = metadata[f"{tenant_id}/{display_path}"]

        if not success:
            raise ValueError(
                f"Could not fetch metadata for the following files: {missing_data_files}"
            )

        return result
