class ServerError(Exception):
    """Raised when a server error occurs"""

    def __init__(self, message):
        super().__init__(message)
