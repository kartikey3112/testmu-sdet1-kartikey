"""Unit tests for response validation and the retry rule.

FIXTURES: model responses here are hand-written strings and `fake_chat` stands in for the
LLM. That is allowed only in tests/unit; the classifier's runtime path always calls the real
API (ai.llm_client.chat). Nothing here is sample output.
"""

import json
from typing import Any

import pytest

from ai.classifier import classify
from ai.llm_client import ChatResult

TEST = {
    "test_id": "tests/api/test_api.py::test_x",
    "case_id": "API-001",
    "signals": {"passed_on_rerun": False, "http_5xx_seen": True},
    "attempts": [{"attempt": 1, "error": {"message": "boom"},
                  "api_last_exchange": {"status": 503}}],
}


def answer(**overrides: Any) -> dict[str, Any]:
    item = {
        "test_id": TEST["test_id"], "case_id": "API-001", "bucket": "environment_issue",
        "confidence": 0.9, "evidence": ["signals.http_5xx_seen: true",
                                        "attempts[0].api_last_exchange.status: 503"],
        "reasoning": "Rule 2 applies. The API returned 503.",
        "suggested_next_action": "Check the service, then re-run.",
    }
    return item | overrides


def as_json(*items: dict[str, Any]) -> str:
    return json.dumps({"classifications": list(items)})


def test_valid_response_is_accepted() -> None:
    valid, problems = classify.validate_response(as_json(answer()), [TEST])

    assert problems == []
    assert valid[TEST["test_id"]].bucket == "environment_issue"


@pytest.mark.parametrize(("text", "expected"), [
    ("not json", "schema"),
    (as_json(answer(bucket="maybe")), "schema"),
    (as_json(answer(confidence=1.5)), "schema"),
    (as_json(answer(evidence=[])), "schema"),
    (as_json(answer(reasoning="One. Two. Three. Four.")), "schema"),
    (as_json(answer(extra_field=1)), "schema"),
    (as_json(answer(case_id="API-999")), "case_id"),
    (as_json(answer(evidence=["signals.made_up_field: 1"])), "evidence"),
    (as_json(answer(evidence=["attempts[5].error.message: x"])), "evidence"),
    (as_json(answer(evidence=["the API was down"])), "evidence"),
    (as_json(answer(), answer()), "more than once"),
    (as_json(answer(test_id="tests/other.py::test_y")), "missing"),
    (json.dumps({"classifications": []}), "missing"),
])
def test_invalid_responses_are_rejected(text: str, expected: str) -> None:
    valid, problems = classify.validate_response(text, [TEST])

    assert TEST["test_id"] not in valid
    assert any(expected in msg for msg in classify.describe(problems))


def fake_chat(responses: list[str]):
    calls: list[list[dict[str, str]]] = []

    def chat(messages: list[dict[str, str]], **_: Any) -> ChatResult:
        calls.append(messages)
        return ChatResult(content=responses[len(calls) - 1], model="fixture", usage={},
                          raw={}, attempts=1, latency_s=0.0, finish_reason="stop")
    return chat, calls


def test_invalid_answer_is_retried_once_with_the_errors() -> None:
    chat, calls = fake_chat(["not json", as_json(answer())])

    valid, call = classify.classify_chunk("prompt", {"tests": [TEST]}, 1, chat_fn=chat)

    assert len(calls) == 2
    assert "Your response was invalid" in calls[1][-1]["content"]
    assert call.attempts == 2
    assert call.valid
    assert TEST["test_id"] in valid


def test_still_invalid_after_retry_leaves_test_unclassified() -> None:
    chat, calls = fake_chat(["not json", "still not json"])

    valid, call = classify.classify_chunk("prompt", {"tests": [TEST]}, 1, chat_fn=chat)

    assert len(calls) == 2  # exactly one retry, never more
    assert valid == {}
    assert not call.valid
    assert call.errors


def test_valid_answer_is_not_retried() -> None:
    chat, calls = fake_chat([as_json(answer())])

    classify.classify_chunk("prompt", {"tests": [TEST]}, 1, chat_fn=chat)

    assert len(calls) == 1


def test_missing_api_key_stops_before_writing(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "")
    (tmp_path / "execution-log.jsonl").write_text("", encoding="utf-8")

    with pytest.raises(classify.LLMConfigError):
        classify.classify_run(tmp_path)

    assert not (tmp_path / "classification.json").exists()


def write_log(run_dir, records: list[dict[str, Any]]) -> None:
    lines = "\n".join(json.dumps(r) for r in records) + "\n"
    (run_dir / "execution-log.jsonl").write_text(lines, encoding="utf-8")


def quota_then_never(messages: list[dict[str, str]], **_: Any) -> ChatResult:
    raise classify.LLMQuotaError("tokens per day exhausted", retry_after_s=900)


def test_quota_exhausted_marks_unsent_tests_unclassified(tmp_path, monkeypatch) -> None:
    from tests.unit.factories import attempt

    monkeypatch.setenv("LLM_API_KEY", "fixture-key")
    write_log(tmp_path, [attempt("t::a"), attempt("t::b")])

    report = classify.classify_run(tmp_path, chat_fn=quota_then_never, budget_chars=1)

    assert [c.bucket for c in report.classifications] == ["unclassified", "unclassified"]
    assert all("quota" in c.reasoning for c in report.classifications)
    assert len(report.llm_calls) == 1  # stopped after the first chunk, did not keep trying


def test_quota_exhausted_raises_when_asked(tmp_path, monkeypatch) -> None:
    from tests.unit.factories import attempt

    monkeypatch.setenv("LLM_API_KEY", "fixture-key")
    write_log(tmp_path, [attempt("t::a")])

    with pytest.raises(classify.LLMQuotaError):
        classify.classify_run(tmp_path, chat_fn=quota_then_never, raise_on_quota=True)

    assert not (tmp_path / "classification.json").exists()


def test_provider_json_rejection_gets_the_same_single_retry() -> None:
    """Groq's JSON mode can reject output itself (HTTP 400 json_validate_failed)."""
    calls: list[list[dict[str, str]]] = []

    def chat(messages: list[dict[str, str]], **_: Any) -> ChatResult:
        calls.append(messages)
        if len(calls) == 1:
            raise classify.LLMInvalidJSONError("json_validate_failed", '{"classifications": [')
        return ChatResult(content=as_json(answer()), model="fixture", usage={}, raw={},
                          attempts=1, latency_s=0.0, finish_reason="stop")

    valid, call = classify.classify_chunk("prompt", {"tests": [TEST]}, 1, chat_fn=chat)

    assert len(calls) == 2
    assert calls[1][-2]["content"] == '{"classifications": ['  # the model's broken output
    assert TEST["test_id"] in valid
    assert call.valid


def test_provider_json_rejection_twice_leaves_test_unclassified() -> None:
    def chat(messages: list[dict[str, str]], **_: Any) -> ChatResult:
        raise classify.LLMInvalidJSONError("json_validate_failed", "{")

    valid, call = classify.classify_chunk("prompt", {"tests": [TEST]}, 1, chat_fn=chat)

    assert valid == {}
    assert call.attempts == 2
    assert not call.valid
