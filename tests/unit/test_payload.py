"""Unit tests for the payload builder: selection, redaction, truncation, chunking.

Inputs are FIXTURES (tests/unit/factories.py), not real run output.
"""

import json

import pytest

from ai.classifier import payload
from app.seed import SEED_USERS
from tests.unit.factories import attempt

JWT = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.c2lnbmF0dXJlLXZhbHVl"


def test_only_tests_with_a_failed_attempt_are_sent() -> None:
    records = [attempt("t::passes", outcome="passed"),
               attempt("t::fails", n=1), attempt("t::fails", n=2)]

    tests = payload.build_tests(records)

    assert [t["test_id"] for t in tests] == ["t::fails"]


@pytest.mark.parametrize("secret_text", [
    f"Authorization: Bearer {JWT}",
    f'{{"access_token": "{JWT}"}}',
    "Cookie: session=abcdef1234567890",
    "/reset-password?token=AbCdEf123456789",
    'password="hunter2-secret"',
    "key gsk_ABCDEFGHIJKLMNOPQRST",
    SEED_USERS[0]["password"],
])
def test_secrets_are_redacted(secret_text: str) -> None:
    redacted = payload.redact_text(f"before {secret_text} after")

    assert "REDACTED" in redacted
    for fragment in (JWT, "abcdef1234567890", "AbCdEf123456789", "hunter2-secret",
                     "gsk_ABCDEFGHIJKLMNOPQRST", SEED_USERS[0]["password"]):
        assert fragment not in redacted


def test_redaction_reaches_nested_fields() -> None:
    api = {"method": "POST", "path": "/api/v1/auth/token", "status": 500,
           "body_snippet": f'{{"access_token":"{JWT}"}}'}

    sent = json.dumps(payload.build_tests([attempt(api=api)]))

    assert JWT not in sent


def test_long_fields_are_cut() -> None:
    record = attempt(message="x" * 5000)

    sent = payload.build_tests([record])[0]["attempts"][0]["error"]["message"]

    assert len(sent) <= payload.MAX_MESSAGE + 3


def test_playwright_call_log_is_removed_from_message() -> None:
    record = attempt(message="Locator expected 'loaded'\nCall log:\n  - waiting ...")

    sent = payload.build_tests([record])[0]["attempts"][0]["error"]["message"]

    assert sent == "Locator expected 'loaded'"


def test_only_first_failed_attempt_has_full_detail() -> None:
    attempts = [attempt(n=i) for i in (1, 2, 3)]

    sent = payload.build_tests(attempts)[0]["attempts"]

    assert "traceback_tail" in sent[0]["error"]
    assert "traceback_tail" not in sent[1]["error"]
    assert sent[1]["error"]["message"] == "assert 1 == 2"


def test_repeated_browser_errors_are_collapsed() -> None:
    ui = {"page_url": "/dashboard", "console_errors": ["503"] * 5, "failed_requests": []}

    sent = payload.build_tests([attempt(ui=ui)])[0]["attempts"][0]["ui"]["console_errors"]

    assert sent == ["503 (x5)"]


def test_local_origin_is_removed_from_urls() -> None:
    ui = {"page_url": "http://127.0.0.1:51234/dashboard", "console_errors": [],
          "failed_requests": ["GET http://127.0.0.1:51234/api/v1/x -> 503"]}

    sent = payload.build_tests([attempt(ui=ui)])[0]["attempts"][0]["ui"]

    assert sent["page_url"] == "/dashboard"
    assert sent["failed_requests"] == ["GET /api/v1/x -> 503"]


def test_chunking_respects_budget_and_keeps_every_test() -> None:
    records = [attempt(f"t::test_{i}", message="m" * 200) for i in range(10)]
    size = len(json.dumps(payload.build_tests(records)[0]))

    chunks = payload.chunk(payload.build_tests(records), budget_chars=size * 3)

    assert [len(c) for c in chunks] == [3, 3, 3, 1]


def test_oversized_test_gets_its_own_chunk() -> None:
    tests = payload.build_tests([attempt("t::a"), attempt("t::b")])

    chunks = payload.chunk(tests, budget_chars=10)

    assert [len(c) for c in chunks] == [1, 1]


def test_every_payload_has_the_whole_run_overview() -> None:
    records = [attempt(f"t::test_{i}") for i in range(4)]

    payloads = payload.build_payloads(records, budget_chars=1)

    assert len(payloads) == 4
    assert all(len(p["failing_tests_overview"]) == 4 for p in payloads)
    assert [p["chunk"] for p in payloads][-1] == {"index": 4, "of": 4}


def test_evaluation_ground_truth_never_reaches_payload() -> None:
    records = [attempt(active_faults_for_evaluation_only=["BUG_X"])]

    assert "BUG_X" not in json.dumps(payload.build_payloads(records))
