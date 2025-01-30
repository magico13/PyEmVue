from datetime import datetime
import time
from typing import Any, Optional, Callable
import jwt
import requests

# These provide AWS cognito authentication support
from pycognito import Cognito

CLIENT_ID = "4qte47jbstod8apnfic0bunmrq"
USER_POOL = "us-east-2_ghlOXVLi1"
USER_POOL_URL = f"https://cognito-idp.us-east-2.amazonaws.com/{USER_POOL}"


class Auth:
    def __init__(
        self,
        host: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        connect_timeout: float = 6.03,
        read_timeout: float = 10.03,
        tokens: Optional["dict[str, Any]"] = None,
        token_updater: Optional[Callable[["dict[str, Any]"], None]] = None,
        max_retry_attempts: int = 5,
        initial_retry_delay: float = 0.5,
        max_retry_delay: float = 30.0,
    ):
        self.host = host
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.token_updater = token_updater
        self.max_retry_attempts = max(max_retry_attempts, 1)
        self.initial_retry_delay = max(initial_retry_delay, 0.5)
        self.max_retry_delay = max(max_retry_delay, 0)
        self.pool_wellknown_jwks = None
        self.tokens = {}

        self._password = None

        if (
            tokens
            and tokens["access_token"]
            and tokens["id_token"]
            and tokens["refresh_token"]
        ):
            # use existing tokens
            self.cognito = Cognito(
                USER_POOL,
                CLIENT_ID,
                user_pool_region="us-east-2",
                id_token=tokens["id_token"],
                access_token=tokens["access_token"],
                refresh_token=tokens["refresh_token"],
            )
        elif username and password:
            # log in with username and password
            self.cognito = Cognito(
                USER_POOL, CLIENT_ID, user_pool_region="us-east-2", username=username
            )
            self._password = password

    def refresh_tokens(self) -> "dict[str, str]":
        """Refresh and return new tokens."""
        if self._password:
            self.cognito.authenticate(password=self._password)

        self.cognito.renew_access_token()
        self._password = None

        tokens = self._extract_tokens_from_cognito()
        self.tokens = tokens

        if self.token_updater is not None:
            self.token_updater(tokens)

        return tokens

    def get_username(self) -> str:
        """Get the username associated with the logged in user."""
        user = self.cognito.get_user()
        return user._data["email"]

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Make a request."""
        if not self.tokens or not self.tokens["access_token"]:
            raise ValueError("Not authenticated. Incorrect username or password?")

        dec_access_token = self._decode_token(self.tokens["access_token"])

        attempts = 0
        while attempts < self.max_retry_attempts:
            attempts += 1
            if datetime.now() > datetime.fromtimestamp(dec_access_token["exp"]):
                # expired, get new tokens
                self.tokens = self.refresh_tokens()

            response = self._do_request(method, path, **kwargs)

            if response.status_code == 401:
                # if unauthorized, try refreshing the tokens
                self.tokens = self.refresh_tokens()
                # then run the request again with updated tokens
                response = self._do_request(method, path, **kwargs)

            if response.status_code >= 500:
                # if server error, retry with exponential backoff
                delay = min(
                    self.initial_retry_delay * (2 ** (attempts - 1)),
                    self.max_retry_delay,
                )
                time.sleep(delay)
                continue

            if response.status_code < 500:
                return response

        return response

    def _extract_tokens_from_cognito(self) -> "dict[str, Any]":
        return {
            "access_token": self.cognito.access_token,
            "id_token": self.cognito.id_token,  # Emporia uses this token for authentication
            "refresh_token": self.cognito.refresh_token,
            "token_type": self.cognito.token_type,
        }

    def _do_request(self, method: str, path: str, **kwargs) -> requests.Response:
        headers = kwargs.get("headers")

        if headers is None:
            headers = {}
        else:
            headers = dict(headers)
        headers["authtoken"] = self.tokens["id_token"]

        return requests.request(
            method,
            f"{self.host}/{path}",
            **kwargs,
            headers=headers,
            timeout=(self.connect_timeout, self.read_timeout),
        )

    def _decode_token(self, token: str, verify_exp: bool = False) -> dict:
        """Decode a JWT token and return the payload as a dictionary, without a hard dependency on pycognito."""
        if not self.pool_wellknown_jwks:
            self.pool_wellknown_jwks = requests.get(
                USER_POOL_URL + "/.well-known/jwks.json",
                timeout=5,
            ).json()

        kid = jwt.get_unverified_header(token).get("kid")
        keys = self.pool_wellknown_jwks.get("keys")
        key = list(filter(lambda x: x.get("kid") == kid, keys))[0]
        hmac_key = jwt.api_jwk.PyJWK(key).key
        return jwt.api_jwt.decode(
            token,
            algorithms=["RS256"],
            key=hmac_key,
            issuer=self.cognito.user_pool_url,
            options={"verify_exp": verify_exp, "verify_iat": False, "verify_nbf": False},
        )

class SimulatedAuth(Auth):
    def __init__(
        self, host: str, username: Optional[str] = None, password: Optional[str] = None
    ):
        self.host = host
        self.username = username
        self.password = password
        self.connect_timeout = 6.03
        self.read_timeout = 10.03
        self.tokens = self.refresh_tokens()

    def refresh_tokens(self) -> dict[str, str]:
        return {"id_token": "simulator"}

    def get_username(self) -> str:
        """Get the username associated with the logged in user."""
        return self.username or "simulator"

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Make a request."""
        response = self._do_request(method, path, **kwargs)

        if response.status_code == 401:
            # if unauthorized, try refreshing the tokens
            self.tokens = self.refresh_tokens()
            # then run the request again with updated tokens
            response = self._do_request(method, path, **kwargs)

        return response
