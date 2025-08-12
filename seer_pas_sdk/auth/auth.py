import atexit
from datetime import datetime
import requests
import jwt
from ..common import get_version
from ..common.errors import ServerError


class Auth:
    _instances = {
        "US": "https://api.pas.seer.software/",
        "EU": "https://api.pas-eu.seer.bio/",
    }

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
            The instance name of the PAS instance (`US | EU`). Defaults to `US`.
        """

        self.username = username
        self.__password = password
        self.version = get_version()

        if instance not in Auth._instances:
            if instance.startswith("https://") or instance.startswith(
                "http://"
            ):
                # Support arbitrary endpoint for testing
                self.url = instance
            else:
                raise ValueError("Invalid PAS instance.")
        else:
            self.url = Auth._instances[instance]
        self.refresh_token = None
        self.refresh_token_expiry = 0
        self.instance = instance

        # Null initialize multi tenant attributes
        (
            self.base_tenant_id,
            self.active_tenant_id,
            self.base_role,
            self.active_role,
        ) = [None] * 4

        atexit.register(self._logout)

    def _login(self):
        """
        Logs into the PAS instance using the mapped URL and the login credentials (username and password) provided in the constructor.

        Returns
        -------
        dict
            A dictionary containing the login response from the PAS instance.
        """
        s = requests.Session()
        s.headers.update(
            {"x-seer-source": "sdk", "x-seer-id": f"{self.version}/login"}
        )
        response = s.post(
            f"{self.url}auth/login",
            json={"username": self.username, "password": self.__password},
        )

        if not response:
            raise ValueError(
                "Check if the credentials are correct or if the backend is running or not."
            )

        if response.status_code == 200:
            return response.json()

    def _logout(self):
        if not self.has_valid_refresh_token():
            print("No valid refresh token found. Skipping logout")
            return True
        s = requests.Session()
        s.headers.update(
            {"x-seer-source": "sdk", "x-seer-id": f"{self.version}/logout"}
        )
        response = s.post(
            f"{self.url}auth/logout",
            json={
                "username": self.username,
                "refreshtoken": self.refresh_token,
            },
        )
        try:
            response.raise_for_status()
        except Exception as e:
            raise ServerError("Could not logout from the PAS instance")
        self.refresh_token = None
        self.refresh_token_expiry = 0
        print(
            f"User {self.username} logged out successfully. Thank you for using the PAS SDK."
        )
        return True

    def _get_refresh_token(self):
        s = requests.Session()
        s.headers.update(
            {
                "x-seer-source": "sdk",
                "x-seer-id": f"{self.version}/refresh_token",
            }
        )
        response = s.post(
            f"{self.url}auth/refreshtoken",
            json={"refreshtoken": self.refresh_token},
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise ServerError("Could not refresh token")

    def get_token(self):
        """
        Refresh or login to the PAS instance to obtain a valid token.

        Returns
        -------
        str
            The token from the login response.
        """
        if self.has_valid_refresh_token():
            res = self._get_refresh_token()
        else:
            res = self._login()

        if "id_token" not in res or "access_token" not in res:
            raise ValueError(
                "Check if the credentials are correct or if the backend is running or not."
            )

        # assign refresh token
        self.refresh_token = res.get("refresh_token", None)
        self.refresh_token_expiry = int(datetime.now().timestamp()) + res.get(
            "expiresIn", 0
        )
        decoded_token = jwt.decode(
            res["id_token"], options={"verify_signature": False}
        )
        self.base_tenant_id = decoded_token["custom:tenantId"]
        self.base_role = decoded_token["custom:role"]

        if not self.active_tenant_id:
            self.active_tenant_id = self.base_tenant_id

        if not self.active_role:
            self.active_role = self.base_role

        return res["id_token"], res["access_token"]

    def has_valid_refresh_token(self):
        """
        Check if the refresh token is valid.

        Returns
        -------
        bool
            True if the refresh token is valid, False otherwise.
        """
        return (
            self.refresh_token is not None
            and self.refresh_token_expiry > int(datetime.now().timestamp())
        )
