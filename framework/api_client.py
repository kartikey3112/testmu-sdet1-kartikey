"""Thin httpx client for /api/v1 with token handling and schema-validation helpers.

Methods return the raw httpx.Response so tests assert on status codes themselves.
Every exchange is reported to `on_exchange`, which the framework uses to keep the last
request/response on the test item for failure reports (and the Task 3 collector).
"""

import re
from collections.abc import Callable
from typing import Any

import httpx

from framework.schemas import ERROR, assert_matches_schema

Exchange = Callable[[httpx.Response], None]

BODY_SNIPPET_CHARS = 500


TOKEN_IN_BODY = re.compile(r'("access_token"\s*:\s*")[^"]+(")')


def describe_exchange(response: httpx.Response) -> dict[str, Any]:
    """The parts of an exchange worth keeping for a failure report.

    Headers are left out (they carry the bearer token) and tokens in the body are redacted.
    """
    return {
        "method": response.request.method,
        "path": response.request.url.raw_path.decode(),
        "status": response.status_code,
        # Redact before truncating, so a cut-off token can't slip past the pattern.
        "body_snippet": TOKEN_IN_BODY.sub(r"\1[REDACTED]\2", response.text)[:BODY_SNIPPET_CHARS],
    }


class ApiClient:
    def __init__(self, base_url: str, *, token: str | None = None,
                 on_exchange: Exchange | None = None) -> None:
        self.token = token
        self.http = httpx.Client(
            base_url=f"{base_url.rstrip('/')}/api/v1",
            timeout=15,
            event_hooks={"response": [self._record]} if on_exchange else {},
        )
        self._on_exchange = on_exchange

    def _record(self, response: httpx.Response) -> None:
        response.read()
        if self._on_exchange:
            self._on_exchange(response)

    def _headers(self, headers: dict[str, str] | None) -> dict[str, str]:
        merged = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        return merged | (headers or {})

    def request(self, method: str, path: str, *, headers: dict[str, str] | None = None,
                **kwargs: Any) -> httpx.Response:
        return self.http.request(method, path, headers=self._headers(headers), **kwargs)

    # --- Auth ---

    def request_token(self, email: str, password: str) -> httpx.Response:
        return self.http.post("/auth/token", json={"email": email, "password": password})

    def login(self, email: str, password: str) -> "ApiClient":
        response = self.request_token(email, password)
        assert response.status_code == 200, f"Token request failed: {response.status_code}"
        self.token = response.json()["access_token"]
        return self

    # --- Test cases ---

    def list_cases(self, **params: Any) -> httpx.Response:
        return self.request("GET", "/test-cases", params=params)

    def get_case(self, case_id: int) -> httpx.Response:
        return self.request("GET", f"/test-cases/{case_id}")

    def create_case(self, body: dict[str, Any]) -> httpx.Response:
        return self.request("POST", "/test-cases", json=body)

    def update_case(self, case_id: int, body: dict[str, Any]) -> httpx.Response:
        return self.request("PATCH", f"/test-cases/{case_id}", json=body)

    def delete_case(self, case_id: int) -> httpx.Response:
        return self.request("DELETE", f"/test-cases/{case_id}")

    # --- Dashboard widgets ---

    def widget(self, name: str, **params: Any) -> httpx.Response:
        return self.request("GET", f"/dashboard/{name}", params=params)

    def close(self) -> None:
        self.http.close()


def assert_error(response: httpx.Response, status: int, code: str) -> None:
    """Assert the status, the standard error body shape and the error code."""
    assert response.status_code == status, (
        f"Expected {status}, got {response.status_code}: {response.text[:300]}"
    )
    body = response.json()
    assert_matches_schema(body, ERROR)
    assert body["error"]["code"] == code
