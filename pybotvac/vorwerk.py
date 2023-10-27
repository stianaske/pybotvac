from .neato import Vendor


class Vorwerk(Vendor):
    name = "vorwerk"
    endpoint = "https://beehive.ksecosys.com/"
    passwordless_endpoint = "https://mykobold.eu.auth0.com/passwordless/start"
    token_endpoint = "https://mykobold.eu.auth0.com/oauth/token"  # nosec
    scope = ["openid", "email", "profile", "read:current_user", "offline_access"]
    audience = "https://mykobold.eu.auth0.com/userinfo"
    source = "vorwerk_auth0"
    cert_path = True
