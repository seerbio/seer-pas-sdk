import os
import requests 

class Auth:
    def __init__(self, username, password, instance="US"):
        """
        Constructor for the Auth class. Uses the username, password and instance name to instantiate the class.

        Parameters
        ----------
        username: str
            The username of the account associated with the PAS instance.
        password: str
            The password of the account associated with the PAS instance.
        instance: str
            The instance name of the PAS instance. Defaults to "US".
        """
        self.instances = { 
            "US": "https://api.pas.seer.software/",
            "EU": "https://api.pas-eu.seer.bio/",
            # remove below before release
            "staging": "https://api.pas.seer-staging.com/",
            "dev": "http://localhost:3006/"
        }

        self.username = username
        self.__password = password

        if instance not in self.instances:
            raise ValueError("Invalid PAS instance.")

        self.instance = instance
        self.url = self.instances[instance]

    def login(self):
        """
        Logs into the PAS instance using the mapped URL and the login credentials (username and password) provided in the constructor.

        Returns
        -------
        dict
            A dictionary containing the login response from the PAS instance.
        """

        response = requests.post(
            f"{self.url}auth/login", 
            json={ 
                "username": self.username, 
                "password": self.__password 
                })

        if not response:
            raise ValueError("Check if the credentials are correct or if the backend is running or not.")

        if response.status_code == 200:
            return response.json()
    
    def get_token(self):
        """
        Gets the token from the login response.

        Returns
        -------
        str
            The token from the login response.
        """

        res = self.login()

        if "id_token" not in res:
            raise ValueError("Check if the credentials are correct or if the backend is running or not.") 
    
        return res['id_token']