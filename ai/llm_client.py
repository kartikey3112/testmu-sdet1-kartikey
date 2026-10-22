"""Single real HTTP client for an OpenAI-compatible chat endpoint, configured via LLM_* env vars.

Works with Groq (default) and Ollama by changing env vars only:
  LLM_BASE_URL  e.g. https://api.groq.com/openai/v1  or  http://localhost:11434/v1
  LLM_API_KEY   required for Groq; any non-empty value for Ollama
  LLM_MODEL     e.g. openai/gpt-oss-120b

The API key is only ever placed in the Authorization header. It is never logged or returned.
"""

import os
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

MAX_RETRIES = 6  # 2+4+8+16+32+60 s of backoff: the free-tier TPM window can need over a minute
BACKOFF_BASE_S = 2.0
MAX_BACKOFF_S = 60.0
# If the provider asks us to wait longer than this, waiting in-process is pointless: on Groq
# it means the daily token limit (TPD) is used up. Fail at once with the provider's message.
GIVE_UP_AFTER_S = 120.0


class LLMConfigError(RuntimeError):
    pass


class LLMError(RuntimeError):
    pass


class LLMQuotaError(LLMError):
    """The provider's quota needs a long wait (e.g. Groq's tokens-per-day limit)."""

    def __init__(self, message: str, retry_after_s: float) -> None:
        super().__init__(message)
        self.retry_after_s = retry_after_s


def requested_wait(response: httpx.Response) -> float | None:
    value = response.headers.get("retry-after")
    try:
        return float(value) if value else None
    except ValueError:
        return None


@dataclass(frozen=True)
class LLMConfig:
    base_url: str
    api_key: str = field(repr=False)
    model: str
    timeout_s: float = 180.0

    @property
    def provider(self) -> str:
        host = httpx.URL(self.base_url).host
        if "groq" in host:
            return "groq"
        if host in ("localhost", "127.0.0.1"):
            return "local (ollama-compatible)"
        return host


def load_llm_config() -> LLMConfig:
    base_url = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
    if not api_key:
        raise LLMConfigError(
            "LLM_API_KEY is not set. Copy .env.example to .env and add a free Groq key "
            "from https://console.groq.com/keys (or point LLM_BASE_URL at Ollama)."
        )
    return LLMConfig(base_url=base_url, api_key=api_key, model=model,
                     timeout_s=float(os.getenv("LLM_TIMEOUT_S", "180")))


@dataclass
class ChatResult:
    content: str
    model: str
    usage: dict[str, Any]
    raw: dict[str, Any]
    attempts: int
    latency_s: float
    finish_reason: str | None = None


def _retry_delay(response: httpx.Response | None, attempt: int) -> float:
    if response is not None:
        retry_after = response.headers.get("retry-after")
        if retry_after:
            try:
                return min(float(retry_after), MAX_BACKOFF_S)
            except ValueError:
                pass
    return min(BACKOFF_BASE_S * 2 ** (attempt - 1), MAX_BACKOFF_S)


def _is_retryable(response: httpx.Response) -> bool:
    if response.status_code == 429 or response.status_code >= 500:
        return True
    # Groq answers "tokens-per-minute window is full" with 413 + code rate_limit_exceeded.
    if response.status_code == 413:
        try:
            return response.json()["error"]["code"] == "rate_limit_exceeded"
        except (ValueError, KeyError, TypeError):
            return False
    return False


def chat(messages: list[dict[str, str]], *, config: LLMConfig | None = None,
         temperature: float = 0, json_mode: bool = True,
         extra: dict[str, Any] | None = None) -> ChatResult:
    """POST /chat/completions. Retries rate limits and 5xx with backoff, honouring Retry-After."""
    config = config or load_llm_config()
    payload: dict[str, Any] = {
        "model": config.model,
        "messages": messages,
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    payload |= extra or {}

    headers = {"Authorization": f"Bearer {config.api_key}"}
    started = time.monotonic()
    with httpx.Client(base_url=config.base_url, timeout=config.timeout_s) as http:
        for attempt in range(1, MAX_RETRIES + 2):
            response = None
            try:
                response = http.post("/chat/completions", json=payload, headers=headers)
            except httpx.TransportError as exc:
                if attempt > MAX_RETRIES:
                    raise LLMError(f"Could not reach {config.base_url}: {exc}") from exc
            else:
                if response.status_code == 200:
                    body = response.json()
                    return ChatResult(
                        content=body["choices"][0]["message"].get("content") or "",
                        model=body.get("model", config.model),
                        usage=body.get("usage", {}),
                        raw=body,
                        attempts=attempt,
                        latency_s=round(time.monotonic() - started, 2),
                        finish_reason=body["choices"][0].get("finish_reason"),
                    )
                retryable = _is_retryable(response)
                wait = requested_wait(response)
                if retryable and wait is not None and wait > GIVE_UP_AFTER_S:
                    raise LLMQuotaError(
                        f"LLM quota exhausted (HTTP {response.status_code}); provider asks to"
                        f" retry in {wait:.0f}s: {response.text[:400]}", wait)
                if not retryable or attempt > MAX_RETRIES:
                    raise LLMError(
                        f"LLM request failed: HTTP {response.status_code}: {response.text[:500]}"
                    )
            # Backoff between API calls (rate limits); not used in tests.
            time.sleep(_retry_delay(response, attempt))
    raise LLMError("unreachable")
