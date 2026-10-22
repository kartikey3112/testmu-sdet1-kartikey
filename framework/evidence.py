"""Per-test evidence gathered while a test runs, used for failure reports.

This is the result-collection hook point for Task 3: the framework fills an Evidence object
for every test attempt and calls the `pytest_testmu_attempt_finished` hook with it. The
Flaky Test Classifier's collector (Phase 5) implements that hook; nothing else needs to change.
"""

from dataclasses import dataclass, field
from typing import Any

import pytest
from playwright.sync_api import ConsoleMessage, Page, Request, Response

MAX_ITEMS = 20


@dataclass
class Evidence:
    pages: list[Page] = field(default_factory=list)
    console_errors: list[str] = field(default_factory=list)
    failed_requests: list[str] = field(default_factory=list)
    last_api_exchange: dict[str, Any] | None = None
    page_url: str | None = None
    screenshot_paths: list[str] = field(default_factory=list)
    trace_paths: list[str] = field(default_factory=list)

    def watch(self, page: Page) -> None:
        """Start recording console errors and failed network requests for a page."""
        self.pages.append(page)

        def on_console(msg: ConsoleMessage) -> None:
            if msg.type == "error":
                self._add(self.console_errors, msg.text)

        def on_request_failed(req: Request) -> None:
            self._add(self.failed_requests, f"{req.method} {req.url} failed: {req.failure}")

        def on_response(resp: Response) -> None:
            if resp.status >= 400:
                line = f"{resp.request.method} {resp.url} -> {resp.status}"
                self._add(self.failed_requests, line)

        page.on("console", on_console)
        page.on("pageerror", lambda err: self._add(self.console_errors, f"pageerror: {err}"))
        page.on("requestfailed", on_request_failed)
        page.on("response", on_response)

    @staticmethod
    def _add(items: list[str], value: str) -> None:
        if len(items) < MAX_ITEMS:
            items.append(value)


EVIDENCE_KEY = pytest.StashKey[Evidence]()


def evidence_for(item: pytest.Item) -> Evidence:
    if EVIDENCE_KEY not in item.stash:
        item.stash[EVIDENCE_KEY] = Evidence()
    return item.stash[EVIDENCE_KEY]


def reset_evidence(item: pytest.Item) -> Evidence:
    """Fresh evidence for a new attempt (reruns reuse the same item)."""
    item.stash[EVIDENCE_KEY] = Evidence()
    return item.stash[EVIDENCE_KEY]
