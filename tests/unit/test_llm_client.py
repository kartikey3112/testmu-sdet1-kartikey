"""Unit tests for how the LLM client reads provider errors. Responses are FIXTURES."""

import httpx

from ai import llm_client


def response(status: int, body: dict, headers: dict | None = None) -> httpx.Response:
    return httpx.Response(status, json=body, headers=headers or {})


def test_groq_json_validate_failed_is_recognised() -> None:
    body = {"error": {"message": "Failed to generate JSON.", "code": "json_validate_failed",
                      "failed_generation": '{"classifications": ['}}

    error = llm_client._invalid_json_error(response(400, body))

    assert isinstance(error, llm_client.LLMInvalidJSONError)
    assert error.failed_generation == '{"classifications": ['


def test_other_400s_are_not_treated_as_invalid_json() -> None:
    body = {"error": {"message": "bad model", "code": "model_not_found"}}

    assert llm_client._invalid_json_error(response(400, body)) is None


def test_per_minute_window_413_is_retryable() -> None:
    body = {"error": {"code": "rate_limit_exceeded", "message": "tokens per minute"}}

    assert llm_client._is_retryable(response(413, body))


def test_long_retry_after_is_read() -> None:
    assert llm_client.requested_wait(response(429, {}, {"retry-after": "884"})) == 884.0
