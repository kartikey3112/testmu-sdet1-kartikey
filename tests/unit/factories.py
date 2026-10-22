"""FIXTURES for unit tests: hand-written execution-log records.

These are not output of a real run and are never used as sample output. They only exist to
test the payload builder, signals and response validation without a browser or an LLM.
"""

from typing import Any


def attempt(nodeid: str = "tests/api/test_api.py::test_x", n: int = 1, outcome: str = "failed",
            message: str = "assert 1 == 2", error_type: str = "AssertionError",
            duration: float = 0.5, health: int | None = 200, **extra: Any) -> dict[str, Any]:
    record: dict[str, Any] = {
        "nodeid": nodeid, "case_id": "API-001", "module": "api", "layer": "api",
        "attempt": n, "outcome": outcome, "duration_s": duration,
    }
    if outcome != "passed":
        record["error"] = {"phase": "call", "type": error_type, "message": message,
                           "location": "tests/api/test_api.py:10",
                           "traceback_tail": "E   " + message, "log_lines": []}
        record["api"] = extra.pop("api", None)
        record["ui"] = extra.pop("ui", None)
        record["health_at_failure"] = (
            {"status": health, "body": "{}"} if health is not None else None)
    record.update(extra)
    return record
