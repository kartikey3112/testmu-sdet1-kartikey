"""Client for the app's TEST_MODE-only endpoints: reset, faults, clock and outbox."""

import re

import httpx

RESET_LINK = re.compile(r"(https?://\S+/reset-password\?token=[\w-]+)")


class TestControl:
    __test__ = False  # not a pytest test class

    def __init__(self, base_url: str) -> None:
        self.http = httpx.Client(base_url=base_url, timeout=10)

    def reset(self, *, keep_sessions: bool = False) -> None:
        self.http.post("/_test/reset", params={"keep_sessions": keep_sessions}).raise_for_status()

    def set_faults(self, *names: str) -> None:
        self.http.post("/_test/faults", json={"faults": list(names)}).raise_for_status()

    def active_faults(self) -> list[str]:
        return self.http.get("/_test/faults").raise_for_status().json()["active"]

    def advance_clock(self, seconds: float) -> None:
        self.http.post("/_test/clock", json={"advance_seconds": seconds}).raise_for_status()

    def outbox(self, to: str | None = None) -> list[dict]:
        params = {"to": to} if to else {}
        return self.http.get("/_test/outbox", params=params).raise_for_status().json()["messages"]

    def latest_reset_link(self, email: str) -> str:
        messages = self.outbox(to=email)
        if not messages:
            raise AssertionError(f"No email in the test outbox for {email}")
        match = RESET_LINK.search(messages[-1]["body"])
        if match is None:
            raise AssertionError(f"No reset link in the latest email to {email}")
        return match.group(1)

    def close(self) -> None:
        self.http.close()
