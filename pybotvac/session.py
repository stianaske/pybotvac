"""Sessionhandling for beehive endpoint."""

import binascii
import json
import os
import os.path
from typing import Callable, Dict, Optional

import requests
from oauthlib.oauth2 import TokenExpiredError
from requests_oauthlib import OAuth2Session

from .exceptions import NeatoException, NeatoLoginException, NeatoRobotException
from .neato import Neato, Vendor
from .vorwerk import Vorwerk

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin


class Session:
    def __init__(self, vendor: Vendor):
        """Initialize the session."""
        self.vendor = vendor
        self.endpoint = vendor.endpoint
        self.headers = {"Accept": vendor.beehive_version}

    def get(self, path, **kwargs):
        """Send a GET request to the specified path."""
        raise NotImplementedError

    def urljoin(self, path):
        return urljoin(self.endpoint, path)

    def generate_headers(
        self, custom_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Merge self.headers with custom headers id necessary."""
        if not custom_headers:
            return self.headers

        return {**self.headers, **custom_headers}


class PasswordSession(Session):
    def __init__(self, email: str, password: str, vendor: Vendor = Neato()):
        super().__init__(vendor=vendor)
        self._login(email, password)

    def _login(self, email: str, password: str):
        """
        Login to pybotvac account using provided email and password.

        :param email: email for pybotvac account
        :param password: Password for pybotvac account
        :return:
        """

        try:
            response = requests.post(
                urljoin(self.endpoint, "sessions"),
                json={
                    "email": email,
                    "password": password,
                    "platform": "ios",
                    "token": binascii.hexlify(os.urandom(64)).decode("utf8"),
                },
                headers=self.headers,
                timeout=10,
            )

            response.raise_for_status()
            access_token = response.json()["access_token"]

            # pylint: disable=consider-using-f-string
            self.headers["Authorization"] = "Token token=%s" % access_token
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
            requests.exceptions.Timeout,
        ) as ex:
            if (
                isinstance(ex, requests.exceptions.HTTPError)
                and ex.response.status_code == 403
            ):
                raise NeatoLoginException(
                    "Unable to login to neato, check account credentials."
                ) from ex
            raise NeatoRobotException("Unable to connect to Neato API.") from ex

    def get(self, path, **kwargs):
        url = self.urljoin(path)
        headers = self.generate_headers(kwargs.pop("headers", None))
        try:
            response = requests.get(url, headers=headers, timeout=10, **kwargs)
            response.raise_for_status()
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
            requests.exceptions.Timeout,
        ) as ex:
            raise NeatoException("Unable to connect to neato the neato serves.") from ex
        return response


class OAuthSession(Session):
    def __init__(
        self,
        token: Optional[Dict[str, str]] = None,
        client_id: str = None,
        client_secret: str = None,
        redirect_uri: str = None,
        token_updater: Optional[Callable[[str], None]] = None,
        vendor: Vendor = Neato(),
    ):
        super().__init__(vendor=vendor)

        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._token_updater = token_updater

        extra = {"client_id": self._client_id, "client_secret": self._client_secret}

        self._oauth = OAuth2Session(
            auto_refresh_kwargs=extra,
            client_id=client_id,
            token=token,
            redirect_uri=redirect_uri,
            token_updater=token_updater,
            scope=vendor.scope,
        )

    def refresh_tokens(self) -> dict:
        """Refresh and return new tokens."""
        token = self._oauth.refresh_token(f"{self.endpoint}/auth/token")

        if self._token_updater is not None:
            self._token_updater(token)

        return token

    def get_authorization_url(self) -> str:
        """Get an authorization url via oauth2."""
        # pylint: disable=unused-variable
        authorization_url, state = self._oauth.authorization_url(
            self.vendor.auth_endpoint
        )
        return authorization_url

    def fetch_token(self, authorization_response: str) -> Dict[str, str]:
        """Fetch an access token via oauth2."""
        token = self._oauth.fetch_token(
            self.vendor.token_endpoint,
            authorization_response=authorization_response,
            client_secret=self._client_secret,
        )
        return token

    def get(self, path: str, **kwargs) -> requests.Response:
        """Make a get request.

        We don't use the built-in token refresh mechanism of OAuth2 session because
        we want to allow overriding the token refresh logic.
        """
        url = self.urljoin(path)
        try:
            response = self._get(url, **kwargs)
            response.raise_for_status()
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
            requests.exceptions.Timeout,
        ) as ex:
            raise NeatoException("Unable to connect to neato the neato serves.") from ex
        return response

    def _get(self, path: str, **kwargs) -> requests.Response:
        """Get request without error handling.

        Refreshes the token if necessary.
        """
        headers = self.generate_headers(kwargs.pop("headers", None))
        try:
            return self._oauth.get(path, headers=headers, **kwargs)
        except TokenExpiredError:
            self._oauth.token = self.refresh_tokens()

            return self._oauth.get(path, headers=self.headers, **kwargs)


class PasswordlessSession(Session):
    def __init__(
        self,
        token: Optional[Dict[str, str]] = None,
        client_id: str = None,
        token_updater: Optional[Callable[[str], None]] = None,
        vendor: Vendor = Vorwerk(),
    ):
        super().__init__(vendor=vendor)

        self._token = token
        self._client_id = client_id
        self._token_updater = token_updater

    def send_email_otp(self, email: str):
        """Request an authorization code via email."""
        response = requests.post(
            self.vendor.passwordless_endpoint,
            data=json.dumps(
                {
                    "client_id": self._client_id,
                    "connection": "email",
                    "email": email,
                    "send": "code",
                }
            ),
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        response.raise_for_status()

    def fetch_token_passwordless(self, email: str, code: str):
        """Fetch an access token using the emailed code."""
        response = requests.post(
            self.vendor.token_endpoint,
            data=json.dumps(
                {
                    "prompt": "login",
                    "grant_type": "http://auth0.com/oauth/grant-type/passwordless/otp",
                    "scope": " ".join(self.vendor.scope),
                    "locale": "en",
                    "otp": code,
                    "source": self.vendor.source,
                    "platform": "ios",
                    "audience": self.vendor.audience,
                    "username": email,
                    "client_id": self._client_id,
                    "realm": "email",
                    "country_code": "DE",
                }
            ),
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        response.raise_for_status()
        self._token = response.json()

    def get(self, path: str, **kwargs) -> requests.Response:
        """Make a get request."""
        url = self.urljoin(path)
        headers = self.generate_headers(kwargs.pop("headers", None))
        # pylint: disable=consider-using-f-string
        headers["Authorization"] = "Auth0Bearer {}".format(self._token.get("id_token"))

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
            requests.exceptions.Timeout,
        ) as ex:
            raise NeatoException("Unable to connect to neato servers.") from ex
        return response
