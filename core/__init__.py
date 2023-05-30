from auth import Auth
from dotenv import load_dotenv
import os
import requests
import json

class SeerSDK:
    def __init__(self):
        """
        Constructor for SeerSDK class. Creates an instance of the Auth class and uses environment variables conatined in the .env file to authenticate a user.
        """

        load_dotenv()
        self.auth = Auth(
            os.getenv("USERNAME"), 
            os.getenv("PASSWORD"), 
            os.getenv("URL"))
    
    def get_token(self):
        """
        Fetches a fresh login authentication token from the API.
        """

        return self.auth.login()['id_token']
        
    def get_analyses(self, page=None, items=None, id=None):
        """
        Returns a list of analyses for the authenticated user, limited by number of pages and items in every page. Pages and items are set to None by default, which returns all analyses unless passed in otherwise.
        """

        TOKEN = self.get_token()
        HEADERS = {"Authorization": f"{TOKEN}"}
        URL = f"{self.auth.url}api/v1/analyses"
        analyses = {}
        
        with requests.Session() as s:
            s.headers.update(HEADERS)

            analyses = s.get(
                f"{URL}/{id}" if id else URL, 
                params={'all': 'true'})
            
            return json.dumps(analyses.json(), indent=4)

    def analyze(self, name, protocol_id, project_id, notes="", description="", user_group_id=None):
        """
        Given a nane, protocol_id, project_id, creates a new analysis for the authenticated user. Returns the analysis object.
        """

        if not name:
            raise ValueError("Analysis name cannot be empty.")
        
        if not protocol_id:
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
                    "analysisProtocolId": protocol_id,
                    "projectId": project_id,
                    "notes": notes,
                    "description": description,
                    "userGroupId": user_group_id
                }
            )

            return json.dumps(analysis.json(), indent=4)    
    
    def download_analysis_data(self, analysis_id):
        """
        Given an analysis id, this function returns all relevant analysis data files in form of downloadable content, if applicable.
        """

        if not analysis_id:
            raise ValueError("Analysis ID cannot be empty.")

        TOKEN = self.get_token()
        HEADERS = {"Authorization": f"{TOKEN}"}
        URL = f"{self.auth.url}api/v1/data"

        with requests.Session() as s:
            s.headers.update(HEADERS)

            protein_data = s.get(
                f"{URL}/protein?analysisId={analysis_id}&retry=false",
            ).json()
            
            peptide_data = s.get(
                f"{URL}/peptide?analysisId={analysis_id}&retry=false",
            ).json()
        
            return json.dumps({
                "Peptide NP": peptide_data["npLink"]["url"],
                "Peptide Panel": peptide_data["panelLink"]["url"],
                "Protein NP": protein_data["npLink"]["url"],
                "Protein Panel": protein_data["panelLink"]["url"],
            }, indent=4)