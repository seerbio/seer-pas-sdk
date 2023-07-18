from common import *
from auth import Auth
from dotenv import load_dotenv
from objects import PlateMap
from tqdm import tqdm

import os
import requests
import json
import uuid
import urllib.request

class SeerSDK:
    def __init__(self, username, password):
        """
        Constructor for SeerSDK class. Creates an instance of the Auth class and uses environment variables conatined in the .env file to authenticate a user.

        Example
        -------

        >>> from core import SeerSDK
        >>> seer_sdk = SeerSDK()
        """

        load_dotenv() # load environment variables from .env file

        try:
            self.auth = Auth(
                username, 
                password, 
                os.getenv("URL"))
            
            print(f"User '{username}' logged in.")
        
        except:
            print("Could not log in.\nPlease check your username and password.")

    def get_spaces(self):
        """
        Fetches a list of spaces for the authenticated user.

        Returns
        -------
        spaces: list
            List of space objects for the authenticated user.

        Example
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

        TOKEN = self.auth.get_token()
        HEADERS = {"Authorization": f"{TOKEN}"}
        URL = f"{self.auth.url}api/v1/usergroups"
        
        with requests.Session() as s:
            s.headers.update(HEADERS)

            spaces = s.get(URL)
            
            if spaces.status_code != 200:
                raise ValueError("Invalid request. Please check your parameters.")
            
            return spaces.json()

    def get_plate_metadata(self, plate_id: str=None, df: bool=False):
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

        Example
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

        TOKEN = self.auth.get_token()
        HEADERS = {"Authorization": f"{TOKEN}"}
        URL = f"{self.auth.url}api/v1/plates"
        res = []
        
        with requests.Session() as s:
            s.headers.update(HEADERS)

            plates = s.get(
                f"{URL}/{plate_id}" if plate_id else URL, 
                params={'all': 'true'})
            
            if plates.status_code != 200:
                raise ValueError("Invalid request. Please check your parameters.")
            
            if not plate_id:
                res = plates.json()["data"]
            else:
                res = [plates.json()]

        return res if not df else dict_to_df(res)
   
    def get_project_metadata(self, project_id: str=None, df: bool=False):
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

        Example
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

        TOKEN = self.auth.get_token()
        HEADERS = {"Authorization": f"{TOKEN}"}
        URL = f"{self.auth.url}api/v1/projects" if not project_id else f"{self.auth.url}api/v1/projects/{project_id}"
        res = []
        
        with requests.Session() as s:
            s.headers.update(HEADERS)

            projects = s.get(
                URL, 
                params={'all': 'true'})
            
            if projects.status_code != 200:
                raise ValueError("Invalid request. Please check your parameters.")
            
            if not project_id:
                res = projects.json()["data"]
            else:
                res = [projects.json()]

        return res if not df else dict_to_df(res)
    
    def get_samples_metadata(self, plate_id: str=None, project_id: str=None, df: bool=False):
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

        Example
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
        TOKEN = self.auth.get_token()
        HEADERS = {"Authorization": f"{TOKEN}"}
        URL = f"{self.auth.url}api/v1/samples"
        sample_params = { 
            "all": "true"
        }

        with requests.Session() as s:
            s.headers.update(HEADERS)

            if plate_id:
                try:
                    self.get_plate_metadata(plate_id) 
                except:
                    raise ValueError("Plate ID is invalid. Please check your parameters and see if the backend is running.")
                
                sample_params["plateId"] = plate_id
            
            elif project_id:
                try: 
                    self.get_project_metadata(project_id)
                except:
                    raise ValueError("Project ID is invalid. Please check your parameters and see if the backend is running.")

                sample_params["projectId"] = project_id

            samples = s.get(
                URL, 
                params=sample_params)
            
            if samples.status_code != 200:
                raise ValueError("Invalid request. Please check if your plate ID has any samples associated with it.")
            
            res = samples.json()["data"]

        return res if not df else dict_to_df(res)

    def get_msdata(self, sample_ids: list, df: bool=False):
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

        Example
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
            TOKEN = self.auth.get_token()
            HEADERS = {"Authorization": f"{TOKEN}"}
            URL = f"{self.auth.url}api/v1/msdatas/items"

            with requests.Session() as s:
                s.headers.update(HEADERS)

                msdatas = s.post(
                    URL,
                    json={
                        "sampleId": sample_id
                    }
                )

                if msdatas.status_code != 200 or not msdatas.json()["data"]:
                    raise ValueError("Failed to fetch MS data for your plate ID.")

                res.append(msdatas.json()["data"][0])

        return res if not df else dict_to_df(res)
        
    def get_plate(self, plate_id: str, df: bool=False):
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

        Example
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

    def get_project(self, project_id: str, msdata: bool=False, df: bool=False):
        """
        Fetches samples (and MS data files) for a `project_id` (provided that the `project_id` is valid and has samples associated with it) for an authenticated user. 

        The function returns a dict containing DataFrame objects if the `df` flag is passed in as True, otherwise a nested dict object is returned instead.

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

        Example
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
        >>> {
                "msdata": [
                    { 
                        "id": "MS_DATA_ID_1_HERE",
                        "raw_file_path": "/directory/one"
                    },
                    { 
                        "id": "MS_DATA_ID_2_HERE",
                        "raw_file_path": "/directory/two"
                    }
                ],
                
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
        
        >>> seer_sdk.get_project(project_id=project_id, msdata=True, df=True)
        >>> {
            'msdata':                                      
                                             id  ... gradient
        0  83365300-8a47-11ed-b382-bf440acece26  ...     None
        1  8335b6c0-8a47-11ed-b382-bf440acece26  ...     None
        2  832e63c0-8a47-11ed-b382-bf440acece26  ...     None
        3  8326e9b0-8a47-11ed-b382-bf440acece26  ...     None

        [4 rows x 26 columns], 
        
        'project_samples':                                                                                 id  ... control
        0  829509f0-8a47-11ed-b382-bf440acece26  ...
        1  828d41c0-8a47-11ed-b382-bf440acece26  ...
        2  8294e2e0-8a47-11ed-b382-bf440acece26  ...
        3  8285eec0-8a47-11ed-b382-bf440acece26  ...

        [4 rows x 59 columns]}

        """
        if not project_id:
            return ValueError("No project ID specified.")

        res = {}
        project_samples = self.get_samples_metadata(project_id=project_id, df=False)

        if msdata:
            sample_ids = [sample["id"] for sample in project_samples]
            res["msdata"] = self.get_msdata(sample_ids=sample_ids, df=df)

        if df:
            project_samples = dict_to_df(project_samples)

        res["project_samples"] = project_samples
        return res        

    def get_analysis_protocols(self, analysis_protocol_name: str=None, analysis_protocol_id: str=None):
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

        Example
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

        TOKEN = self.auth.get_token()
        HEADERS = {"Authorization": f"{TOKEN}"}
        URL = f"{self.auth.url}api/v1/analysisProtocols" if not analysis_protocol_id else f"{self.auth.url}api/v1/analysisProtocols/{analysis_protocol_id}"
        
        with requests.Session() as s:
            s.headers.update(HEADERS)

            protocols = s.get(
                URL, 
                params={'all': 'true'})
            
            if protocols.status_code != 200:
                raise ValueError("Invalid request. Please check your parameters.")
            
            if not analysis_protocol_id and not analysis_protocol_name:
                return protocols.json()["data"]

            if analysis_protocol_name and not analysis_protocol_id:
                return [protocol for protocol in protocols.json()["data"] if protocol["analysis_protocol_name"] == analysis_protocol_name]
            
            return [protocols.json()] 

    def get_analysis(self, analysis_id: str=None):
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

        Example
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

        TOKEN = self.auth.get_token()
        HEADERS = {"Authorization": f"{TOKEN}"}
        URL = f"{self.auth.url}api/v1/analyses"
        
        with requests.Session() as s:
            s.headers.update(HEADERS)

            analyses = s.get(
                f"{URL}/{analysis_id}" if analysis_id else URL, 
                params={'all': 'true'})
            
            if analyses.status_code != 200:
                raise ValueError("Invalid request. Please check your parameters.")
            
            if not analysis_id:
                return analyses.json()["data"]

            return [analyses.json()["analysis"]]
    
    def get_analysis_result(self, analysis_id: str, download_path: str=""):
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
        
        Example
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
                raise ValueError("Cannot generate links for failed or null analyses.")

        TOKEN = self.auth.get_token()
        HEADERS = {"Authorization": f"{TOKEN}"}
        URL = f"{self.auth.url}api/v1/data"

        with requests.Session() as s:
            s.headers.update(HEADERS)

            protein_data = s.get(
                f"{URL}/protein?analysisId={analysis_id}&retry=false"
            )

            if protein_data.status_code != 200:
                raise ValueError("Invalid request. Could not fetch protein data. Please check your parameters.")
            
            protein_data = protein_data.json()

            peptide_data = s.get(
                f"{URL}/peptide?analysisId={analysis_id}&retry=false"
            )

            if peptide_data.status_code != 200:
                raise ValueError("Invalid request. Could not fetch peptide data. Please check your parameters.")

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
                links["peptide_panel"].to_csv(f"{name}/peptide_panel.csv", sep="\t")
                links["protein_np"].to_csv(f"{name}/protein_np.csv", sep="\t")
                links["protein_panel"].to_csv(f"{name}/protein_panel.csv", sep="\t")

                return { "status": "Download complete." }

            return links

    def add_sample(self, plate_id: str, sample_id: str, sample_name: str, space: str=None):
        """
        Add a sample given a plate_id, sample_id, sample_name and space.

        Parameters
        ----------
        plate_id : str
            The plate ID.
        sample_id : str
            The sample ID.
        sample_name : str   
            The sample name.
        space : str 
            The space.

        Returns
        -------
        dict
            The response from the backend.
        
        Example
        -------
        >>> from core import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.add_sample("YOUR_PLATE_ID_HERE", "YOUR_SAMPLE_ID_HERE", "YOUR_SAMPLE_NAME_HERE")
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
        if not "plate_id":
            raise ValueError("Plate ID cannot be empty.")
        
        if not "sample_id":
            raise ValueError("Sample ID cannot be empty.")

        if not "sample_name":
            raise ValueError("Sample name cannot be empty.")


        TOKEN = self.auth.get_token()
        HEADERS = {"Authorization": f"{TOKEN}"}
        URL = f"{self.auth.url}api/v1/samples"

        with requests.Session() as s:
            s.headers.update(HEADERS)

            response = s.post(
                URL,
                json={ 
                    "plateID": plate_id,
                    "sampleID": sample_id,
                    "sampleName": sample_name,
                    "sampleUserGroup": space
                }
            )

            if response.status_code != 200:
                raise ValueError("Invalid request. Please check your parameters.")
            
            return response.json()

    def add_project(self, project_name: str, plate_ids: list[str], description: str=None, notes: str=None, space: str=None):

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

        Example
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

        TOKEN = self.auth.get_token()
        HEADERS = {"Authorization": f"{TOKEN}"}
        URL = f"{self.auth.url}api/v1/projects"

        with requests.Session() as s:
            s.headers.update(HEADERS)

            project = s.post(
                URL,
                json={
                    "projectName": project_name,
                    "plateIDs": plate_ids,
                    "notes": notes,
                    "description": description,
                    "projectUserGroup": space
                }
            )

            if project.status_code != 200:
                raise ValueError("Invalid request. Please check your parameters.")
            
            res = { "status": f"Project started with id = {project.json()['id']}" }

            return res

    def add_plate(self, ms_data_files: list[str], plate_map_file: str, plate_id: str, plate_name: str, sample_description_file: str=None, space: str=None):
        """
        Add a plate given a list of ms_data_files, plate_map_file, plate_id, plate_name, sample_description_file and space.

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
        res : dict
            A dictionary containing the status of the request if succeeded.

        Example
        -------
        >>> from core import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.add_plate(["MS_DATA_FILE_1", "MS_DATA_FILE_2"], "PLATE_MAP_FILE", "PLATE_ID", "PLATE_NAME")
        >>> {
                "status": "Plate with id = PLATE_ID started."
            }
        """
    
        TOKEN = self.auth.get_token()
        HEADERS = {"Authorization": f"{TOKEN}"}

        plate_ids = set() # contains all the plate_ids fetched from self.get_plate_metadata()
        files = [] # to be uploaded to sync frontend
        samples = [] # list of all the sample responses from the backend
        id_uuid = "" # uuid for the plate id
        raw_file_paths = {} # list of all the AWS raw file paths
        s3_upload_path = None
        s3_bucket = ""
        
        # Step 1: Check for duplicacy in the user-inputted plate id. Populates `plate_ids` set.

        with requests.Session() as s:
            s.headers.update(HEADERS)
            plate_response = s.get(f"{self.auth.url}api/v1/plateids")

            if plate_response.status_code != 200:
                raise ValueError("Cannot connect to the server.")

            plate_ids = set(plate_response.json()["data"])            

            if not plate_ids:
                raise ValueError("Cannot connect to the server.")
        
        # Step 2: Fetch the UUID that needs to be passed into the backend from `/api/v1/plates` to fetch the AWS upload config and raw file path. This will sync the plates backend with samples when the user uploads later. This UUID will also be void of duplicates since duplication is handled by the backend.

        with requests.Session() as s:
            s.headers.update(HEADERS)
            plate_response = s.post(
                f"{self.auth.url}api/v1/plates",
                json={ 
                    "plateId": plate_id,
                    "plateName": plate_name,
                    "plateUserGroup": space
                })

            if plate_response.status_code != 200:
                raise ValueError("Cannot connect to the server while fetching plates.")
            
            id_uuid = plate_response.json()["id"]
        
            if not id_uuid:
                raise ValueError("Cannot connect to the server while fetching plates.")
        
        # Step 3: Fetch AWS upload config from the backend with the plateId we just generated. Populates `s3_upload_path` and `s3_bucket` global variables.
        with requests.Session() as s:
            s.headers.update(HEADERS)
            config_response = s.post(
                f"{self.auth.url}api/v1/msdatas/getuploadconfig", 
                json={ 
                    "plateId": id_uuid
                })

            if config_response.status_code != 200 or not config_response.json():
                raise ValueError("Upload failed, please check if backend is still running.")

            if "s3Bucket" not in config_response.json() or "s3UploadPath" not in config_response.json():
                raise ValueError("Upload failed. Please check if the backend is still running.") 

            s3_bucket = config_response.json()["s3Bucket"]
            s3_upload_path = config_response.json()["s3UploadPath"]

        # Step 4: Upload the platemap file to the S3 bucket.

        if isinstance(plate_map_file, PlateMap):
            plate_map_file_name = f"plateMap_{id_uuid}.csv"
            plate_map_file.to_csv(f"testing/{plate_map_file_name}")
            plate_map_file = f"testing/{plate_map_file_name}"
            
        else:
            plate_map_file_name = os.path.basename(plate_map_file)

        res = upload_file(plate_map_file, s3_bucket, f"{s3_upload_path}{plate_map_file_name}")

        if not res:
            raise ValueError("Platemap upload failed.")
        
        with requests.Session() as s:
            s.headers.update(HEADERS)
            plate_map_response = s.post(
                f"{self.auth.url}api/v1/msdataindex/file", 
                json={ 
                    "files": [{ 
                        "filePath": f"{s3_upload_path}{plate_map_file_name}",
                        "fileSize": os.stat(plate_map_file).st_size,
                        "userGroupId": space 
                    }]
                })

            if plate_map_response.status_code != 200 or not plate_map_response.json() or "created" not in plate_map_response.json():
                raise ValueError("Upload failed, please check if backend is still active and running.")

        # Step 5: Populate `raw_file_paths` for sample upload.
        for file in ms_data_files:
            filename = os.path.basename(file)
            filesize = os.stat(file).st_size
            raw_file_paths[f"{filename}"] = f"/{s3_bucket}/{s3_upload_path}{filename}"
        
        # Step 6: Get sample info from the plate map file and make a call to `/api/v1/samples` with the sample_info. This returns the plateId, sampleId and sampleName for each sample in the plate map file.
        sample_info = get_sample_info(id_uuid, ms_data_files, plate_map_file, space)

        for entry in sample_info:
            sample = self.add_sample(entry["plateID"], entry["sampleID"], entry["sampleName"], entry["sampleUserGroup"])
            samples.append(sample)

        # Step 7: Parse the plate map file and convert the data into a form that can be POSTed to `/api/v1/msdatas`.
        plate_map_data = parse_plate_map_file(plate_map_file, samples, raw_file_paths, space)

        # Step 8: Make a request to `/api/v1/msdatas` with the processed samples data.
        for file_index in range(len(ms_data_files)):
            file = ms_data_files[file_index]
            
            with requests.Session() as s:
                s.headers.update(HEADERS)
                ms_data_response = s.post(
                    f"{self.auth.url}api/v1/msdatas",
                    json=plate_map_data[file_index]
                )

                if ms_data_response.status_code != 200:
                    raise ValueError("Upload failed, please check if backend is still active and running.")

        # Step 9: Upload each msdata file to the S3 bucket.
        for file in ms_data_files:
            filename = os.path.basename(file)
            filesize = os.stat(file).st_size
            res = upload_file(file, s3_bucket, f"{s3_upload_path}{filename}")

            if not res:
                raise ValueError("Upload to AWS S3 failed.")

            files.append({
                "filePath": f"{s3_upload_path}{filename}",
                "fileSize": filesize,
                "userGroupId": space
            })     

        # Step 10: Make a call to `api/v1/msdataindex/file` to sync with frontend. This should only be done after all files have finished uploading, simulating an async "promise"-like scenario in JavaScript.
        with requests.Session() as s:
            s.headers.update(HEADERS)
            file_response = s.post(
                f"{self.auth.url}api/v1/msdataindex/file", 
                json={ 
                    "files": files
                })

            if file_response.status_code != 200 or not file_response.json() or "created" not in file_response.json():
                raise ValueError("Upload failed, please check if backend is still active and running.")

        return {
            "message": f"Plate generated with id = {id_uuid}"
        }
    
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

        Example
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
        
        return { "status": res[0]["status"] }

    def start_analysis(self, name: str, project_id: str, analysis_protocol_name: str=None, analysis_protocol_id: str=None, notes: str="", description: str="", space: str=None):
        """
        Given a name, analysis_protocol_id, project_id, creates a new analysis for the authenticated user.

        Parameters
        ----------
        name : str
            Name of the analysis.

        project_id : str
            ID of the project to which the analysis belongs. Can be fetched using the get_project_metadata() function.

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

        Returns
        -------
        dict
            Contains message whether the analysis was started or not.

        Example
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
            valid_analysis_protocol = self.get_analysis_protocols(analysis_protocol_name)

            if not valid_analysis_protocol:
                raise ValueError("Analysis protocol not found. Your protocol name is incorrect.")
            
            analysis_protocol_id = valid_analysis_protocol[0]["id"]

        if analysis_protocol_id and not analysis_protocol_name:
            valid_analysis_protocol = self.get_analysis_protocols(analysis_protocol_id)
            
            if not valid_analysis_protocol:
                raise ValueError("Analysis protocol not found. Your protocol ID is incorrect.")

        if not analysis_protocol_id and not analysis_protocol_name:
            raise ValueError("You must specify either analysis protocol ID or analysis protocol name. Both cannot be empty.")

        TOKEN = self.auth.get_token()
        HEADERS = {"Authorization": f"{TOKEN}"}
        URL = f"{self.auth.url}api/v1/analyze"

        with requests.Session() as s:
            s.headers.update(HEADERS)

            analysis = s.post(
                URL,
                json={
                    "analysisName": name,
                    "analysisProtocolId": analysis_protocol_id,
                    "projectId": project_id,
                    "notes": notes,
                    "description": description,
                    "userGroupId": space
                }
            )

            if analysis.status_code != 200:
                raise ValueError("Invalid request. Please check your parameters.")

            return analysis.json()

    def upload_ms_data_files(self, ms_data_files: list, path: str="", space: str=None):
        """
        Upload MS data files to the backend.

        Parameters
        ----------
        ms_data_files : List
            List of MS data files to be uploaded.
        space: str, optional
            ID of the user group to which the files belongs, defaulted to None.

        Returns 
        -------
        dict
            Contains message whether the files were uploaded or not.

        Example
        -------
        >>> from core import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.upload_ms_data_files(["/path/to/file1", "/path/to/file2"])
        >>> { "message": "Files uploaded successfully." }
        """

        files = []
        tenant_id = ""
        s3_bucket = ""

        # Step 1: Check if paths and file extensions are valid.
        for file in ms_data_files:
            if not valid_ms_data_file(file):
                raise ValueError("Invalid file or file format. Please check your file.")

        # Step 2: Fetch the tenant id by making a call to `/api/v1/usersetting`
        TOKEN = self.auth.get_token()
        HEADERS = {"Authorization": f"{TOKEN}"}
        URL = f"{self.auth.url}api/v1/usersetting"

        with requests.Session() as s:
            s.headers.update(HEADERS)
            response = s.get(URL)

            if response.status_code != 200:
                raise ValueError("Could not connect to the backend.")

            tenant_id = response.json()["tenant_id"]

        # Step 3: Fetch the S3 bucket name by making a call to `/api/v1/auth/getawscredential`
        with requests.Session() as s:
            s.headers.update(HEADERS)
            config_response = s.get(
                f"{self.auth.url}auth/getawscredential",)

            if config_response.status_code != 200 or not config_response.json():
                raise ValueError("Could not fetch config for user.")

            if "S3Bucket" not in config_response.json()["credentials"]:
                raise ValueError("Upload failed. Please check if the backend is still running.") 

            s3_bucket = config_response.json()["credentials"]["S3Bucket"]

        # Step 4: Upload each msdata file to the S3 bucket.
        for file in ms_data_files:
            filename = os.path.basename(file)
            filesize = os.stat(file).st_size
            s3_upload_path = f"{tenant_id}/{path}"

            res = upload_file(file, s3_bucket, f"{s3_upload_path}/{filename}")

            if not res:
                raise ValueError("Upload to AWS S3 failed.")

            files.append({
                "filePath": f"{s3_upload_path}/{filename}",
                "fileSize": filesize,
                "userGroupId": space
            })   
        
        # Step 5: Make a call to `/api/v1/msdataindex/file` to sync with frontend. This should only be done after all files have finished uploading, simulating an async "promise"-like scenario in JavaScript.
        with requests.Session() as s:
            s.headers.update(HEADERS)
            file_response = s.post(
                f"{self.auth.url}api/v1/msdataindex/file", 
                json={ 
                    "files": files
                })

            if file_response.status_code != 200 or not file_response.json() or "created" not in file_response.json():
                raise ValueError("Upload failed, please check if backend is still active and running.")

        return { "message": "Files uploaded successfully." }
    
    def download_analysis_files(self, analysis_id: str, download_path: str="", file_name: str=""):
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

        Example
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
            TOKEN = self.auth.get_token()
            HEADERS = {"Authorization": f"{TOKEN}"}
            URL = f"{self.auth.url}api/v1/analysisResultFiles/getUrl" 

            with requests.Session() as s:
                s.headers.update(HEADERS)

                download_url = s.post(
                    URL,
                    json={
                        "analysisId": analysis_id,
                        "filename": file_name,
                        "projectId": project_id
                    })

                if download_url.status_code != 200:
                    raise ValueError("Could not download file. Please check if the analysis ID is valid or the backend is running.")

                return download_url.json()["url"]

        if not analysis_id:
            raise ValueError("Analysis ID cannot be empty.")

        try:
            valid_analysis = self.get_analysis(analysis_id)[0]
        except:
            raise ValueError("Invalid analysis ID. Please check if the analysis ID is valid or the backend is running.")

        project_id = valid_analysis["project_id"]

        if not download_path:
            download_path = os.getcwd()
            print(f"\nDownload path not specified, downloading to {download_path}/downloads/{analysis_id}\n")

        if not os.path.isdir(download_path):
            download_path = os.getcwd()
            print(f"\nThe path you entered was invalid. Downloading to current working directory at {download_path}/downloads/{analysis_id}\n")

        name = f"{download_path}/downloads/{analysis_id}"
        
        if not os.path.exists(name):
            os.makedirs(name)

        TOKEN = self.auth.get_token()
        HEADERS = {"Authorization": f"{TOKEN}"}
        URL = f"{self.auth.url}api/v1/analysisResultFiles"

        with requests.Session() as s:
            s.headers.update(HEADERS)

            analysis_files = s.get(f"{URL}/{analysis_id}")

            if analysis_files.status_code != 200:
                raise ValueError("Invalid request. Please check if the analysis ID is valid or the backend is running.")
            
            res = analysis_files.json()

        if file_name:
            filenames = set([file["filename"] for file in res])

            if file_name not in filenames:
                raise ValueError("Invalid file name. Please check if the file name is correct.")
            
            res = [file for file in res if file["filename"] == file_name]

        for file in res:
            filename = file["filename"]
            name = f"{download_path}/downloads/{analysis_id}"
            url = get_url(analysis_id, filename, project_id)

            print(f"Downloading {filename}") 

            for _ in range(2):
                try:
                    with tqdm(unit = 'B', unit_scale = True, unit_divisor = 1024, miniters = 1, desc = f"Progress") as t:
                        urllib.request.urlretrieve(url, f"{name}/{filename}", reporthook=download_hook(t), data=None)
                        break
                except:
                    filename = filename.split("/")
                    name += "/" + "/".join([filename[i] for i in range(len(filename) - 1)])
                    filename = filename[-1]
                    if not os.path.isdir(f"{name}/{filename}"):
                        os.makedirs(f"{name}/")
            
            else:
                raise ValueError("Your download failed. Please check if the backend is still running.")

            print(f"Finished downloading {filename}\n") 

        return { "message": f"Files downloaded successfully to {download_path}/downloads/{analysis_id}" }