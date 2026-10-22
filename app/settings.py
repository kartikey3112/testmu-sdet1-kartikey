"""Runtime settings (from env vars) and the app clock.

Every threshold is configurable by env var. The clock can be shifted forward through
the test-only API, so expiry rules can be tested without waiting in real time.
"""

import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


@dataclass(frozen=True)
class Settings:
    test_mode: bool
    db_path: Path
    lockout_threshold: int
    lockout_minutes: int
    session_ttl_seconds: int
    reset_token_minutes: int
    token_ttl_seconds: int
    rate_limit_per_min: int
    jwt_secret: str
    flaky_latency_seconds: float
    flaky_latency_probability: float


def load_settings() -> Settings:
    return Settings(
        test_mode=os.getenv("TEST_MODE", "0") == "1",
        db_path=Path(os.getenv("DB_PATH", "testmu.sqlite3")),
        lockout_threshold=_int("LOCKOUT_THRESHOLD", 5),
        lockout_minutes=_int("LOCKOUT_MINUTES", 15),
        session_ttl_seconds=_int("SESSION_TTL_SECONDS", 1800),
        reset_token_minutes=_int("RESET_TOKEN_MINUTES", 30),
        token_ttl_seconds=_int("TOKEN_TTL_SECONDS", 3600),
        rate_limit_per_min=_int("RATE_LIMIT_PER_MIN", 60),
        jwt_secret=os.getenv("JWT_SECRET", "testmu-lite-dev-secret-not-for-production"),
        flaky_latency_seconds=float(os.getenv("FLAKY_LATENCY_SECONDS", "7")),
        flaky_latency_probability=float(os.getenv("FLAKY_LATENCY_PROBABILITY", "0.3")),
    )


settings = load_settings()


class Clock:
    """Wall clock plus an offset that only the test-only API can change."""

    def __init__(self) -> None:
        self.offset = timedelta(0)

    def now(self) -> datetime:
        return datetime.now(UTC) + self.offset

    def advance(self, seconds: float) -> None:
        self.offset += timedelta(seconds=seconds)

    def reset(self) -> None:
        self.offset = timedelta(0)


clock = Clock()
