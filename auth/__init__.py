from dotenv import load_dotenv
import os
import requests 

class Auth:
    def __init__(self, username, password, url):
        self.username = username
        self.__password = password
        self.url = url

    def login(self):
        response = requests.post(
            f"{self.url}auth/login", 
            json={ 
                "username": self.username, 
                "password": self.__password 
                })

        if not response:
            return { 
                "error": "Check if the credentials are correct or if the backend is running or not."
            }

        if response.status_code == 200:
            return response.json()
    
    def get_token(self):
        res = self.login()

        if "id_token" not in res:
            raise ValueError("Check if the credentials are correct or if the backend is running or not.") 
    
        return res['id_token']