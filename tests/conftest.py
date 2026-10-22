"""Shared fixtures: app server process, role-based browser contexts, API client.

Markers for module and layer come from the folder a test lives in, so tests don't repeat
them: tests/ui/login -> ui + login, tests/api -> api, tests/unit -> unit.
"""

from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import Browser, BrowserContext, Page

from framework.api_client import ApiClient, describe_exchange
from framework.app_server import AppServer
from framework.config import config, credentials
from framework.evidence import evidence_for
from framework.pytest_plugin import artifact_dir, run_dir, test_failed
from framework.sessions import RoleSessions
from framework.test_control import TestControl

FOLDER_MARKERS = {"ui": "ui", "api": "api", "unit": "unit", "login": "login",
                  "dashboard": "dashboard"}


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        for part in Path(item.path).parts:
            if part in FOLDER_MARKERS:
                item.add_marker(FOLDER_MARKERS[part])


# --- App under test --------------------------------------------------------------------------

@pytest.fixture(scope="session")
def app_server(request: pytest.FixtureRequest, tmp_path_factory) -> Iterator[str]:
    """Base URL of a running TestMu Lite. Starts one unless TESTMU_BASE_URL is set."""
    if config.external_base_url:
        yield config.external_base_url.rstrip("/")
        return
    server = AppServer(
        db_path=tmp_path_factory.mktemp("db") / "testmu.sqlite3",
        log_path=run_dir(request.config) / "app-server.log",
    )
    server.start(config.server_start_timeout_s)
    try:
        yield server.base_url
    finally:
        server.stop()


@pytest.fixture(scope="session")
def base_url(app_server: str) -> str:
    """Overrides pytest-base-url so Playwright's page.goto('/login') resolves to the app."""
    return app_server


@pytest.fixture(scope="session")
def test_control(base_url: str) -> Iterator[TestControl]:
    control = TestControl(base_url)
    yield control
    control.close()


@pytest.fixture(autouse=True)
def clean_app(request: pytest.FixtureRequest) -> None:
    """Every UI/API test starts from seed data, no faults beyond FAULTS env, real clock.

    Logged-in sessions are kept so cached role logins stay usable.
    """
    if request.node.get_closest_marker("unit"):
        return
    request.getfixturevalue("test_control").reset(keep_sessions=True)


# --- API -------------------------------------------------------------------------------------

def _api(request: pytest.FixtureRequest, base_url: str, role: str | None) -> ApiClient:
    def record(response) -> None:
        evidence_for(request.node).last_api_exchange = describe_exchange(response)

    client = ApiClient(base_url, on_exchange=record)
    if role:
        user = credentials(role)
        client.login(user.email, user.password)
    request.addfinalizer(client.close)
    return client


@pytest.fixture
def api_client(request: pytest.FixtureRequest, base_url: str) -> ApiClient:
    """Unauthenticated client."""
    return _api(request, base_url, None)


@pytest.fixture
def admin_api(request: pytest.FixtureRequest, base_url: str) -> ApiClient:
    return _api(request, base_url, "admin")


@pytest.fixture
def viewer_api(request: pytest.FixtureRequest, base_url: str) -> ApiClient:
    return _api(request, base_url, "viewer")


# --- Browser ---------------------------------------------------------------------------------

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict[str, Any]) -> dict[str, Any]:
    return {**browser_context_args, "viewport": {"width": 1280, "height": 800}}


@pytest.fixture(scope="session")
def role_sessions(base_url: str) -> RoleSessions:
    return RoleSessions(base_url)


NewPage = Callable[..., Page]


@pytest.fixture
def new_page(
    request: pytest.FixtureRequest, browser: Browser, browser_context_args: dict[str, Any],
    role_sessions: RoleSessions,
) -> Iterator[NewPage]:
    """Factory: new_page(role=None, viewport=None) -> Page in its own traced context.

    Every page is watched for console errors and failed requests. On failure, the trace is
    kept under the run's artifacts folder and linked from the HTML report.
    """
    contexts: list[tuple[BrowserContext, Path]] = []
    evidence = evidence_for(request.node)

    def make(role: str | None = None, viewport: dict[str, int] | None = None) -> Page:
        args = dict(browser_context_args)
        if viewport:
            args["viewport"] = viewport
        if role:
            args["storage_state"] = role_sessions.storage_state(role)
        context = browser.new_context(**args)
        context.tracing.start(screenshots=True, snapshots=True, sources=False)
        trace_path = artifact_dir(request.node) / f"trace-{len(contexts)}.zip"
        evidence.trace_paths.append(str(trace_path))
        contexts.append((context, trace_path))
        page = context.new_page()
        evidence.watch(page)
        return page

    yield make

    failed = test_failed(request.node)
    for context, trace_path in contexts:
        context.tracing.stop(path=trace_path if failed else None)
        context.close()


@pytest.fixture
def page(new_page: NewPage) -> Page:
    """Anonymous (logged-out) page. Overrides pytest-playwright's page fixture."""
    return new_page()


@pytest.fixture
def admin_page(new_page: NewPage) -> Page:
    return new_page(role="admin")


@pytest.fixture
def viewer_page(new_page: NewPage) -> Page:
    return new_page(role="viewer")
