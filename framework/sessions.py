"""Cached browser logins per role, handed to Playwright as storage_state.

Logging in through the UI for every test is slow and tests the login page over and over.
Instead each role logs in once over HTTP and the session cookie is reused. Before each use
the session is checked; if a test expired it (e.g. by moving the app clock), it logs in again.
"""

from typing import Any
from urllib.parse import urlparse

import httpx

from app.auth import SESSION_COOKIE
from framework.config import credentials


class RoleSessions:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.host = urlparse(base_url).hostname
        self._tokens: dict[str, str] = {}

    def storage_state(self, role: str) -> dict[str, Any]:
        token = self._tokens.get(role)
        if token is None or not self._is_valid(token):
            token = self._login(role)
            self._tokens[role] = token
        return {
            "cookies": [{
                "name": SESSION_COOKIE, "value": token, "domain": self.host, "path": "/",
                "expires": -1, "httpOnly": True, "secure": False, "sameSite": "Lax",
            }],
            "origins": [],
        }

    def _is_valid(self, token: str) -> bool:
        response = httpx.get(
            f"{self.base_url}/dashboard", cookies={SESSION_COOKIE: token},
            follow_redirects=False, timeout=10,
        )
        # Only a redirect to /login means the session is gone. Other errors (e.g. an injected
        # database fault) are left for the test itself to hit and report.
        return not response.is_redirect

    def _login(self, role: str) -> str:
        user = credentials(role)
        response = httpx.post(
            f"{self.base_url}/login", data={"email": user.email, "password": user.password},
            follow_redirects=False, timeout=10,
        )
        token = response.cookies.get(SESSION_COOKIE)
        if response.status_code != 303 or not token:
            raise RuntimeError(f"Could not log in as {role}: HTTP {response.status_code}")
        return token
