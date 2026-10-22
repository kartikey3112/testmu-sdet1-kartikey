"""Env-driven settings for the test framework (base URL, timeouts, credentials source).

Credentials are not duplicated here: they come from the app's seed config (app/seed.py),
so there is one place that defines the test users.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from app.seed import SEED_USERS

load_dotenv()


@dataclass(frozen=True)
class FrameworkConfig:
    # When set, tests run against this already-running app instead of starting one.
    external_base_url: str | None
    # Playwright web-first assertion timeout. The FLAKY_WIDGET_LATENCY fault is set above this.
    expect_timeout_ms: int
    server_start_timeout_s: float
    reports_dir: str
    run_id: str | None


def load_config() -> FrameworkConfig:
    return FrameworkConfig(
        external_base_url=os.getenv("TESTMU_BASE_URL") or None,
        expect_timeout_ms=int(os.getenv("EXPECT_TIMEOUT_MS", "5000")),
        server_start_timeout_s=float(os.getenv("SERVER_START_TIMEOUT_S", "30")),
        reports_dir=os.getenv("REPORTS_DIR", "reports"),
        run_id=os.getenv("TESTMU_RUN_ID") or None,
    )


config = load_config()


@dataclass(frozen=True)
class Credentials:
    email: str
    password: str
    role: str
    name: str


def credentials(role: str) -> Credentials:
    for user in SEED_USERS:
        if user["role"] == role:
            return Credentials(user["email"], user["password"], user["role"], user["name"])
    raise KeyError(f"No seed user with role {role!r}")
