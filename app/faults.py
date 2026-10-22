"""Fault injection: fault names and their ground-truth bucket (single source of truth).

Faults are enabled with the FAULTS env var (comma-separated names) or, when TEST_MODE=1,
with POST /_test/faults. The classifier evaluation reads FAULT_BUCKETS to know the true
cause of each failure; the active faults are never sent to the LLM.
"""

import os
from enum import StrEnum


class Bucket(StrEnum):
    REAL_BUG = "real_bug"
    ENVIRONMENT_ISSUE = "environment_issue"
    FLAKY = "flaky"


FAULT_BUCKETS: dict[str, Bucket] = {
    # Pass-rate widget reads the previous run instead of the latest one.
    "BUG_PASS_RATE_OFF_BY_ONE": Bucket.REAL_BUG,
    # DELETE /api/v1/test-cases/{id} returns 204 but the row stays.
    "BUG_DELETE_NOT_PERSISTED": Bucket.REAL_BUG,
    # Account locks after threshold + 1 failures instead of threshold.
    "BUG_LOCKOUT_THRESHOLD_WRONG": Bucket.REAL_BUG,
    # Dashboard widget endpoints return 503 as if a downstream service is down.
    "ENV_WIDGET_API_503": Bucket.ENVIRONMENT_ISSUE,
    # Every database connection fails; unhandled, so requests return 500.
    "ENV_DB_UNAVAILABLE": Bucket.ENVIRONMENT_ISSUE,
    # /health reports failure while the rest of the app still works.
    "ENV_HEALTH_FAILING": Bucket.ENVIRONMENT_ISSUE,
    # Dashboard widget endpoints sometimes respond slower than the default UI timeout.
    "FLAKY_WIDGET_LATENCY": Bucket.FLAKY,
    # Recent-runs rows come back in random order when no sort is given.
    "FLAKY_UNSORTED_ORDER": Bucket.FLAKY,
}


class UnknownFaultError(ValueError):
    pass


def _parse(names: list[str]) -> set[str]:
    cleaned = {n.strip() for n in names if n.strip()}
    unknown = sorted(cleaned - FAULT_BUCKETS.keys())
    if unknown:
        raise UnknownFaultError(f"Unknown fault(s): {', '.join(unknown)}")
    return cleaned


_active: set[str] = _parse(os.getenv("FAULTS", "").split(","))
_from_env: frozenset[str] = frozenset(_active)


def is_active(name: str) -> bool:
    return name in _active


def active() -> list[str]:
    return sorted(_active)


def set_active(names: list[str]) -> None:
    global _active
    _active = _parse(names)


def reset() -> None:
    """Restore the faults that were set by env var at startup."""
    global _active
    _active = set(_from_env)
