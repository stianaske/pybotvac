import os
from dataclasses import dataclass
from typing import List, Union


@dataclass(init=False, frozen=True)
class Vendor:
    name: str
    endpoint: str
    auth_endpoint: str
    passwordless_endpoint: str
    token_endpoint: str
    scope: List[str]
    audience: str
    source: str
    cert_path: Union[str, bool] = False
    beehive_version: str = "application/vnd.neato.beehive.v1+json"
    nucleo_version: str = "application/vnd.neato.nucleo.v1"


class Neato(Vendor):
    name = "neato"
    endpoint = "https://beehive.neatocloud.com/"
    auth_endpoint = "https://apps.neatorobotics.com/oauth2/authorize"
    token_endpoint = "https://beehive.neatocloud.com/oauth2/token"  # nosec
    scope = ["public_profile", "control_robots", "maps"]
    cert_path = None
