import requests
import jwt


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

        self.instance = instance

        # Null initialize multi tenant attributes
        (
            self.base_tenant_id,
            self.active_tenant_id,
            self.base_role,
            self.active_role,
        ) = [None] * 4

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
            json={"username": self.username, "password": self.__password},
        )

        if not response:
            raise ValueError(
                "Check if the credentials are correct or if the backend is running or not."
            )

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

        if "id_token" not in res or "access_token" not in res:
            raise ValueError(
                "Check if the credentials are correct or if the backend is running or not."
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
