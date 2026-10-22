"""Deterministic pre-signals computed from a test's attempts.

These go to the LLM as hints, not verdicts. Computing them in code means the model doesn't
have to count attempts or compare error strings itself, and a reviewer can check them.
"""

import re
import statistics
from typing import Any

# Normalise volatile parts of error messages before comparing attempts.
_VOLATILE = [
    (re.compile(r"https?://[\w.:-]+"), "<url>"),
    (re.compile(r"\b0x[0-9a-f]+\b", re.I), "<hex>"),
    (re.compile(r"\b\d+(\.\d+)?\b"), "<n>"),
    (re.compile(r"'[^']*'|\"[^\"]*\""), "<str>"),
    (re.compile(r"\s+"), " "),
]

_CATEGORIES = [
    ("timeout", re.compile(r"timeout|timed out|exceeded", re.I)),
    ("connection", re.compile(r"connect(ion)?(error| refused| reset)|ECONNREFUSED|"
                              r"RemoteProtocolError|ConnectError|net::ERR", re.I)),
    ("5xx", re.compile(r"\b5\d\d\b|internal_error|service_unavailable|upstream_unavailable|"
                       r"Internal Server Error", re.I)),
    ("assertion", re.compile(r"AssertionError|assert ", re.I)),
]


def normalise(message: str | None) -> str:
    text = message or ""
    for pattern, replacement in _VOLATILE:
        text = pattern.sub(replacement, text)
    return text.strip()


def error_category(error: dict[str, Any] | None) -> str:
    """timeout / connection / 5xx / assertion / other, from the error type and message.

    Order matters: an assertion about a 503 status is a 5xx, and a Playwright expect() that
    timed out waiting is a timeout, even though both are AssertionErrors.
    """
    if not error:
        return "other"
    # First line only: Playwright appends a call log ("... with timeout 5000ms") to every
    # expect() failure, which would make every UI assertion look like a timeout.
    first_line = (error.get("message") or "").split("\n", 1)[0]
    text = f"{error.get('type', '')}: {first_line}"
    for name, pattern in _CATEGORIES:
        if pattern.search(text):
            return name
    return "other"


_STATUS_5XX = re.compile(r"(?:->\s*|status(?: of)?\s*)5\d\d\b|\b5\d\d \(", re.I)


def saw_5xx(attempt: dict[str, Any]) -> bool:
    """Any server error in this attempt: API status, browser network log or error text.

    A UI test often fails as a Playwright timeout while the real cause is a 503 that only
    shows up in the page's network log, so the error category alone misses it.
    """
    api = attempt.get("api") or {}
    if isinstance(api.get("status"), int) and api["status"] >= 500:
        return True
    ui = attempt.get("ui") or {}
    lines = [*ui.get("failed_requests", []), *ui.get("console_errors", [])]
    error = attempt.get("error") or {}
    lines.append(error.get("message") or "")
    return any(_STATUS_5XX.search(line) for line in lines)


def _health_ok(attempt: dict[str, Any]) -> bool | None:
    health = attempt.get("health_at_failure")
    if not health:
        return None
    return health.get("status") == 200


def compute(attempts: list[dict[str, Any]]) -> dict[str, Any]:
    """Signals for one test, from all of its attempts in attempt order."""
    attempts = sorted(attempts, key=lambda a: a["attempt"])
    failed = [a for a in attempts if a["outcome"] != "passed"]
    durations = [a["duration_s"] for a in attempts]
    messages = {normalise((a.get("error") or {}).get("message")) for a in failed}
    categories = sorted({error_category(a.get("error")) for a in failed})
    health = [_health_ok(a) for a in failed]
    known_health = [h for h in health if h is not None]

    return {
        "attempts": len(attempts),
        "failed_attempts": len(failed),
        "final_outcome": attempts[-1]["outcome"],
        "passed_on_rerun": attempts[-1]["outcome"] == "passed" and bool(failed),
        "same_error_all_attempts": len(failed) == len(attempts) and len(messages) == 1,
        "error_category_heuristic": categories[0] if len(categories) == 1 else categories,
        "http_5xx_seen": any(saw_5xx(a) for a in failed),
        "health_ok_at_failure": all(known_health) if known_health else None,
        "duration_s": {
            "min": min(durations),
            "max": max(durations),
            "spread": round(max(durations) - min(durations), 3),
            "stdev": round(statistics.pstdev(durations), 3),
        },
    }
