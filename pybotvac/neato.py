import os
from dataclasses import dataclass


@dataclass(init=False, frozen=True)
class Vendor:
    name: str
    endpoint: str
    auth_endpoint: str
    passwordless_endpoint: str
    token_endpoint: str
    scope: list[str]
    audience: str
    source: str
    cert_path: str | bool = False
    beehive_version: str = "application/vnd.neato.beehive.v1+json"
    nucleo_version: str = "application/vnd.neato.nucleo.v1"


class Neato(Vendor):
    name = "neato"
    endpoint = "https://beehive.neatocloud.com/"
    auth_endpoint = "https://apps.neatorobotics.com/oauth2/authorize"
    token_endpoint = "https://beehive.neatocloud.com/oauth2/token"  # noqa: S105
    scope = ["public_profile", "control_robots", "maps"]
    cert_path = os.path.join(os.path.dirname(__file__), "cert", "neatocloud.com.crt")
