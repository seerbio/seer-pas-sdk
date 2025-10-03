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
        self.id_token = None
        self.access_token = None
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

        try:
            response.raise_for_status()
        except Exception as e:
            raise ServerError("Could not login to the PAS instance")

        res = response.json()
        mfa_challenge = res.get("challenge", None)
        if mfa_challenge:
            mfa_args = {}
            if any(
                x not in res
                for x in ["challenge", "session", "challengeParameters"]
            ):
                raise ServerError(
                    "Unexpected return from server during MFA challenge. Please check the PAS SDK version and update the PAS SDK if necessary."
                )
            mfa_args["challengeName"] = res["challenge"]
            mfa_args["session"] = res["session"]
            mfa_args["username"] = res["challengeParameters"].get(
                "USER_ID_FOR_SRP", ""
            )
            if not mfa_args["username"]:
                raise ServerError(
                    "Unexpected return from server during MFA challenge. Please check the PAS SDK version and update the PAS SDK if necessary."
                )
            print(
                "Multi-factor authentication (MFA) is enabled for your account."
            )
            mfa_code = input(
                "Please enter the code from your authenticator app:"
            )
            mfa_response = s.post(
                f"{self.url}auth/confirmMFA",
                json={
                    "username": mfa_args["username"],
                    "mfaCode": mfa_code,
                    "challengeName": mfa_args["challengeName"],
                    "session": mfa_args["session"],
                },
            )
            if mfa_response.status_code != 200:
                raise ServerError(
                    "Could not confirm MFA for the PAS instance."
                )
            mfa_response = mfa_response.json()
            if "AuthenticationResult" not in mfa_response:
                raise ServerError(
                    "Unexpected return from server during MFA confirmation. Please check the PAS SDK version and update the PAS SDK if necessary."
                )
            mfa_response = mfa_response["AuthenticationResult"]
            if any(
                x not in mfa_response
                for x in [
                    "AccessToken",
                    "IdToken",
                    "ExpiresIn",
                    "RefreshToken",
                ]
            ):
                raise ServerError(
                    "Unexpected return from server during MFA confirmation. Please check the PAS SDK version and update the PAS SDK if necessary."
                )
            res["id_token"] = mfa_response["IdToken"]
            res["access_token"] = mfa_response["AccessToken"]
            res["expiresIn"] = mfa_response["ExpiresIn"]
            res["refresh_token"] = mfa_response["RefreshToken"]

        decoded_token = jwt.decode(
            res["id_token"], options={"verify_signature": False}
        )
        self.base_tenant_id = decoded_token["custom:tenantId"]
        self.base_role = decoded_token["custom:role"]

        if not self.active_tenant_id:
            self.active_tenant_id = self.base_tenant_id

        if not self.active_role:
            self.active_role = self.base_role

        self.id_token = res["id_token"]
        self.access_token = res["access_token"]
        self.refresh_token = res.get("refresh_token", None)
        self.token_expiry = int(datetime.now().timestamp()) + res.get(
            "expiresIn", 0
        )
        return res["id_token"], res["access_token"]

    def _logout(self):
        if not self.has_valid_token():
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
        self.token_expiry = 0
        print(
            f"User {self.username} logged out successfully. Thank you for using the PAS SDK."
        )
        return True

    def _refresh_token(self):
        """Refreshes the token using the refresh token.

        Raises:
            ServerError: If the token could not be refreshed.

        Returns:
            dict: The response from the server containing the new token.
        """
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
        Gets the current token. If the token is expired, it refreshes the token using the refresh token.

        Returns
        -------
        str
            The token from the login response.
        """
        if self.has_valid_token():
            return self.id_token, self.access_token
        else:
            res = self._refresh_token()

        if "id_token" not in res or "access_token" not in res:
            raise ValueError(
                "Check if the credentials are correct or if the backend is running or not."
            )
        self.token_expiry = int(datetime.now().timestamp()) + res.get(
            "expiresIn", 0
        )

        self.id_token = res["id_token"]
        self.access_token = res["access_token"]
        return res["id_token"], res["access_token"]

    def has_valid_token(self):
        """
        Check if the id and access tokens are valid.

        Returns
        -------
        bool
            True if the refresh token is valid, False otherwise.
        """
        return (
            self.access_token is not None
            and self.id_token is not None
            and self.token_expiry > int(datetime.now().timestamp())
        )
