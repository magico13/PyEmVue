from datetime import datetime
from typing import Any, Optional, Callable
from jose import jwt
import requests

# These provide AWS cognito authentication support
from pycognito import Cognito
import requests

CLIENT_ID = '4qte47jbstod8apnfic0bunmrq'
USER_POOL = 'us-east-2_ghlOXVLi1'

class Auth:
    def __init__(
        self,
        host: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        connect_timeout: float = 6.03,
        read_timeout: float = 10.03,
        tokens: Optional['dict[str, Any]'] = None,
        token_updater: Optional[Callable[['dict[str, Any]'], None]] = None
    ):
        self.host = host
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.token_updater = token_updater

        if tokens and tokens['access_token'] and tokens['id_token'] and tokens['refresh_token']:
            # use existing tokens
            self.cognito = Cognito(USER_POOL, CLIENT_ID,
                user_pool_region='us-east-2', 
                id_token=tokens['id_token'], 
                access_token=tokens['access_token'], 
                refresh_token=tokens['refresh_token'])
        elif username and password:
            #log in with username and password
            self.cognito = Cognito(USER_POOL, CLIENT_ID, 
                user_pool_region='us-east-2', username=username)
            self.cognito.authenticate(password=password)

        self.tokens = self.refresh_tokens()

    def refresh_tokens(self) -> 'dict[str, str]':
        """Refresh and return new tokens."""
        self.cognito.renew_access_token()
        tokens = self._extract_tokens_from_cognito()

        if self.token_updater is not None:
            self.token_updater(tokens)

        return tokens

    def get_username(self) -> str:
        """Get the username associated with the logged in user."""
        user = self.cognito.get_user()
        return user._data['email']

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Make a request."""
        #pycognito's method for checking expiry, but without the hard dependency on the cognito object
        now = datetime.now()
        dec_access_token = jwt.get_unverified_claims(self.tokens['access_token'])

        if now > datetime.fromtimestamp(dec_access_token["exp"]):
            # expired, get new tokens
            self.tokens = self.refresh_tokens()

        response = self._do_request(method, path, **kwargs)

        if response.status_code == 401:
            # if unauthorized, try refreshing the tokens
            self.tokens = self.refresh_tokens()
            # then run the request again with updated tokens
            response = self._do_request(method, path, **kwargs)

        return response

    def _extract_tokens_from_cognito(self) -> 'dict[str, Any]':
        return {
            'access_token': self.cognito.access_token,
            'id_token': self.cognito.id_token, # Emporia uses this token for authentication
            'refresh_token': self.cognito.refresh_token,
            'token_type': self.cognito.token_type
        }

    def _do_request(self, method: str, path: str, **kwargs) -> requests.Response:
        headers = kwargs.get("headers")

        if headers is None:
            headers = {}
        else:
            headers = dict(headers)
        headers["authtoken"] = self.tokens['id_token']

        return requests.request(
            method, f"{self.host}/{path}", **kwargs, headers=headers,
            timeout=(self.connect_timeout, self.read_timeout),
        )
