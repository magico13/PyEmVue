"""Tests for credential validation in Auth and PyEmVue.login."""

from __future__ import annotations

import pytest

from pyemvue.auth import Auth
from pyemvue.pyemvue import API_ROOT, PyEmVue


@pytest.mark.parametrize(
    ("username", "password", "tokens"),
    [
        (None, None, None),
        ("", "", None),
        ("   ", "secret", None),
        ("user@example.com", "", None),
        ("user@example.com", "   ", None),
        (
            None,
            None,
            {"access_token": "", "id_token": "id", "refresh_token": "ref"},
        ),
        (None, None, {"access_token": "acc"}),
    ],
)
def test_auth_rejects_blank_or_incomplete_credentials(
    username: str | None,
    password: str | None,
    tokens: dict[str, str] | None,
) -> None:
    """Auth.refresh_tokens raises ValueError instead of AttributeError when cognito is unset."""
    auth = Auth(host=API_ROOT, username=username, password=password, tokens=tokens)
    with pytest.raises(ValueError, match="non-empty username and password"):
        auth.refresh_tokens()


@pytest.mark.parametrize(
    ("username", "password"),
    [
        (None, None),
        ("", ""),
        ("   ", "secret"),
        ("user@example.com", ""),
    ],
)
def test_pyemvue_login_rejects_blank_credentials(
    username: str | None,
    password: str | None,
) -> None:
    """PyEmVue.login raises ValueError instead of AttributeError on blank credentials."""
    vue = PyEmVue()
    with pytest.raises(ValueError, match="non-empty username and password"):
        vue.login(username=username, password=password)
    if not username or not username.strip():
        assert vue.username is None
