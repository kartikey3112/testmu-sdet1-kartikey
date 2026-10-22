"""Unit tests for deterministic pre-signals. Inputs are FIXTURES (tests/unit/factories.py)."""

from ai.classifier import signals
from tests.unit.factories import attempt


def test_passed_on_rerun() -> None:
    result = signals.compute([attempt(n=1), attempt(n=2, outcome="passed")])

    assert result["passed_on_rerun"] is True
    assert result["final_outcome"] == "passed"
    assert result["failed_attempts"] == 1


def test_same_error_ignores_volatile_numbers_and_urls() -> None:
    result = signals.compute([
        attempt(n=1, message="expected 24 at http://127.0.0.1:5000/x"),
        attempt(n=2, message="expected 25 at http://127.0.0.1:6123/x"),
    ])

    assert result["same_error_all_attempts"] is True


def test_different_errors_are_not_the_same() -> None:
    result = signals.compute([attempt(n=1, message="first row was run A"),
                              attempt(n=2, message="widget never loaded")])

    assert result["same_error_all_attempts"] is False


def test_category_uses_first_line_only() -> None:
    message = "Locator expected to have attribute 'loaded'\nCall log:\n  with timeout 5000ms"

    assert signals.error_category({"type": "AssertionError", "message": message}) == "assertion"


def test_categories() -> None:
    assert signals.error_category({"type": "TimeoutError", "message": "Timeout 30000ms"}) \
        == "timeout"
    assert signals.error_category({"type": "ConnectError", "message": "refused"}) == "connection"
    assert signals.error_category({"type": "AssertionError",
                                   "message": "Expected 200, got 503"}) == "5xx"
    assert signals.error_category(None) == "other"


def test_http_5xx_seen_in_browser_network_log() -> None:
    ui = {"failed_requests": ["GET /api/v1/dashboard/pass-rate -> 503"], "console_errors": []}

    result = signals.compute([attempt(n=1, ui=ui)])

    assert result["http_5xx_seen"] is True


def test_http_5xx_not_seen_for_4xx() -> None:
    api = {"method": "GET", "path": "/x", "status": 404, "body_snippet": ""}

    assert signals.compute([attempt(n=1, api=api)])["http_5xx_seen"] is False


def test_health_ok_unknown_when_not_recorded() -> None:
    assert signals.compute([attempt(n=1, health=None)])["health_ok_at_failure"] is None
    assert signals.compute([attempt(n=1, health=503)])["health_ok_at_failure"] is False
