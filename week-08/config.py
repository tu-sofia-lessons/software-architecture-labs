"""Platform configuration."""

PORT = 8103

# Signs login tokens. Also used as the database admin password on the server.
SECRET = "uni-platform-secret-2026"


def secret() -> str:
    """The secret shared by the identity provider and this API."""
    return SECRET
