from auth import Auth
from dotenv import load_dotenv
import os
import requests
import json

class SeerSDK:
    def __init__(self):
        """
        Constructor for SeerSDK class. Creates an instance of the Auth class and uses environment variables conatined in the .env file to authenticate a user.

        Example
        -------

        >>> from core import SeerSDK
        >>> seer_sdk = SeerSDK()
        """

        load_dotenv() # load environment variables from .env file

        self.auth = Auth(
            os.getenv("USERNAME"), 
            os.getenv("PASSWORD"), 
            os.getenv("URL"))
    
    def get_token(self):
        """
        Fetches a fresh login authentication token from the API.

        Parameters
        ----------
        None

        Returns
        -------
        id_token: str
            Authentication token.

        Example
        -------
        >>> from core import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.get_token()
        >>> "YOUR_ID_TOKEN_HERE"
        """

        return self.auth.login()['id_token']
        
    def get_usergroups(self):
        """
        Fetches a list of usergroups for the authenticated user.

        Returns
        -------
        usergroups: list
            List of usergroup objects for the authenticated user.

        Example
        -------
        >>> from core import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.get_usergroups()
        >>> [
                { "usergroup_name": ... },
                { "usergroup_name": ... },
                ...
            ]
        """

        TOKEN = self.get_token()
        HEADERS = {"Authorization": f"{TOKEN}"}
        URL = f"{self.auth.url}api/v1/usergroups"
        
        with requests.Session() as s:
            s.headers.update(HEADERS)

            usergroups = s.get(URL)
            
            if usergroups.status_code != 200:
                raise ValueError("Invalid request. Please check your parameters.")
            
            return usergroups.json()

    def get_plates(self, id=None):
        """
        Fetches a list of plates for the authenticated user. If no id is provided, returns all plates for the authenticated user. If id is provided, returns the plate with the given id, provided it exists.

        Parameters
        ----------
        id : str, optional
            ID of the plate to be fetched, defaulted to None.

        Returns
        -------
        plates: list
            List of plate objects for the authenticated user.

        Example
        -------
        >>> from core import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.get_plates()
        >>> [
                { "id": ... },
                { "id": ... },
                ...
            ]

        >>> seer_sdk.get_plates(id="YOUR_PLATE_ID_HERE")
        >>> [{ "id": ... }]
        """

        TOKEN = self.get_token()
        HEADERS = {"Authorization": f"{TOKEN}"}
        URL = f"{self.auth.url}api/v1/plates"
        
        with requests.Session() as s:
            s.headers.update(HEADERS)

            plates = s.get(
                f"{URL}/{id}" if id else URL, 
                params={'all': 'true'})
            
            if plates.status_code != 200:
                raise ValueError("Invalid request. Please check your parameters.")
            
            if not id:
                return plates.json()["data"]
            
            return [plates.json()]

    def get_projects(self, id: str=None):
        """
        Fetches a list of projects for the authenticated user. If no id is provided, returns all projects for the authenticated user. If id is provided, returns the project with the given id, provided it exists.

        Parameters
        ----------
        id : str, optional
            ID of the project to be fetched, defaulted to None.

        Returns
        -------
        projects: list
            List of project objects for the authenticated user.

        Example
        -------
        >>> from core import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.get_projects()
        >>> [
                { "project_name": ... },
                { "project_name": ... },
                ...
            ]

        >>> seer_sdk.get_projects(id="YOUR_PROJECT_ID_HERE")
        >>> [{ "project_name": ... }]

        """

        TOKEN = self.get_token()
        HEADERS = {"Authorization": f"{TOKEN}"}
        URL = f"{self.auth.url}api/v1/projects" if not id else f"{self.auth.url}api/v1/projects/{id}"
        
        with requests.Session() as s:
            s.headers.update(HEADERS)

            projects = s.get(
                URL, 
                params={'all': 'true'})
            
            if projects.status_code != 200:
                raise ValueError("Invalid request. Please check your parameters.")
            
            if not id:
                return projects.json()["data"]

            return [projects.json()]
    
    def get_analysis_protocols(self, id: str=None, name: str=None):
        """
        Fetches a list of analysis protocols for the authenticated user. If no id is provided, returns all analysis protocols for the authenticated user. If name (and no id) is provided, returns the analysis protocol with the given name, provided it exists. 
        
        If both name and id are provided, then the function ignores the name and returns the analysis protocol with the given id.

        Parameters
        ----------
        id : str, optional
            ID of the analysis protocol to be fetched, defaulted to None.

        name : str, optional
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

        TOKEN = self.get_token()
        HEADERS = {"Authorization": f"{TOKEN}"}
        URL = f"{self.auth.url}api/v1/analysisProtocols" if not id else f"{self.auth.url}api/v1/analysisProtocols/{id}"
        
        with requests.Session() as s:
            s.headers.update(HEADERS)

            protocols = s.get(
                URL, 
                params={'all': 'true'})
            
            if protocols.status_code != 200:
                raise ValueError("Invalid request. Please check your parameters.")
            
            if not id and not name:
                return protocols.json()["data"]

            if name and not id:
                return [protocol for protocol in protocols.json()["data"] if protocol["analysis_protocol_name"] == name]
            
            return [protocols.json()]
    
    def get_analyses(self, id: str=None):
        """
        Returns a list of analyses objects for the authenticated user. If no id is provided, returns all analyses for the authenticated user.

        Parameters
        ----------
        id : str, optional
            ID of the analysis to be fetched, defaulted to None.
        
        Returns
        -------
        analyses: dict
            Contains a list of analyses objects for the authenticated user.

        Example
        -------
        >>> from core import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.get_analyses()
        >>> [ 
                {id: "YOUR_ANALYSIS_ID_HERE", ...}, 
                {id: "YOUR_ANALYSIS_ID_HERE", ...},
                {id: "YOUR_ANALYSIS_ID_HERE", ...}
            ]

        >>> seer_sdk.get_analyses("YOUR_ANALYSIS_ID_HERE")
        >>> [{ id: "YOUR_ANALYSIS_ID_HERE", ...}]
        """

        TOKEN = self.get_token()
        HEADERS = {"Authorization": f"{TOKEN}"}
        URL = f"{self.auth.url}api/v1/analyses"
        
        with requests.Session() as s:
            s.headers.update(HEADERS)

            analyses = s.get(
                f"{URL}/{id}" if id else URL, 
                params={'all': 'true'})
            
            if analyses.status_code != 200:
                raise ValueError("Invalid request. Please check your parameters.")
            
            if not id:
                return analyses.json()["data"]

            return [analyses.json()["analysis"]]

    def start_analysis(self, name: str, project_id: str, analysis_protocol_id: str, notes: str="", description: str="", user_group_id: str=None):
        """
        Given a name, analysis_protocol_id, project_id, creates a new analysis for the authenticated user.

        Parameters
        ----------
        name : str
            Name of the analysis.

        project_id : str
            ID of the project to which the analysis belongs. Can be fetched using the get_projects() function.

        analysis_protocol_id : str
            ID of the analysis protocol to be used for the analysis. Can be fetched using the get_analysis_protocols() function.

        notes : str, optional
            Notes for the analysis, defaulted to an empty string.

        description : str, optional
            Description for the analysis, defaulted to an empty string.

        user_group_id : str, optional
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
        
        if not analysis_protocol_id:
            raise ValueError("Protocol ID cannot be empty.")
        
        if not project_id:
            raise ValueError("Project ID cannot be empty.")

        TOKEN = self.get_token()
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
                    "userGroupId": user_group_id
                }
            )

            if analysis.status_code != 200:
                raise ValueError("Invalid request. Please check your parameters.")

            return analysis.json()
    
    def download_analysis_data(self, analysis_id: str):
        """
        Given an analysis id, this function returns all relevant analysis data files in form of downloadable content, if applicable.

        Parameters
        ----------
        analysis_id : str
            ID of the analysis for which the data is to be fetched.

        Returns
        -------
        links: dict
            Contains the URLs for the downloadable content.
        
        Example
        -------
        >>> from core import SeerSDK
        >>> seer_sdk = SeerSDK()
        >>> seer_sdk.download_analysis_data("YOUR_ANALYSIS_ID_HERE")
        >>> {
                "peptide_np": "http://aws.amazon.com/your_peptide_np_link_here",
                "peptide_panel": "http://aws.amazon.com/your_peptide_panel_link_here",
                "protein_np": "http://aws.amazon.com/your_protein_np_link_here",
                "protein_panel": "http://aws.amazon.com/your_protein_panel_link_here"
            }
        """

        if not analysis_id:
            raise ValueError("Analysis ID cannot be empty.")

        if self.get_analyses(analysis_id)[0]["analysis"]["status"] in ["FAILED", None]:
                raise ValueError("Cannot generate links for failed or null analyses.")

        TOKEN = self.get_token()
        HEADERS = {"Authorization": f"{TOKEN}"}
        URL = f"{self.auth.url}api/v1/data"

        with requests.Session() as s:
            s.headers.update(HEADERS)

            protein_data = s.get(
                f"{URL}/protein?analysisId={analysis_id}&retry=false",
            )

            if protein_data.status_code != 200:
                raise ValueError("Invalid request. Could not fetch protein data. Please check your parameters.")
            
            protein_data = protein_data.json()

            peptide_data = s.get(
                f"{URL}/peptide?analysisId={analysis_id}&retry=false",
            )

            if peptide_data.status_code != 200:
                raise ValueError("Invalid request. Could not fetch peptide data. Please check your parameters.")

            peptide_data = peptide_data.json()
        
            links = {
                "peptide_np": peptide_data["npLink"]["url"],
                "peptide_panel": peptide_data["panelLink"]["url"],
                "protein_np": protein_data["npLink"]["url"],
                "protein_panel": protein_data["panelLink"]["url"],
            }

            return links
