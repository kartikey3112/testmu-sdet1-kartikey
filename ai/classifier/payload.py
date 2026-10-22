"""Builds the compact, redacted, chunked payload sent to the LLM.

Only tests with at least one failed attempt are sent. Secrets are redacted, long fields are
cut, and tests are packed into chunks that fit the model's budget. Every chunk carries a
short overview of all failing tests in the run, so the model can still see run-wide patterns
(for example "everything failed with 5xx") when the details are split across calls.

Run metadata such as active faults is never read here: those are the evaluation's ground
truth and must not leak into the model's input.
"""

import json
import os
import re
from collections import defaultdict
from typing import Any

from ai.classifier import signals
from app.seed import SEED_USERS

MAX_MESSAGE = 300
MAX_TRACEBACK = 500
MAX_LOG_LINES = 5
MAX_LINE = 200
MAX_LIST_ITEMS = 5
MAX_BODY = 300
# About 2,000 tokens per chunk (4 characters per token). The free Groq tier allows 8,000
# tokens per minute for prompt + payload + answer together.
DEFAULT_CHUNK_CHARS = 8_000

REDACTED = "[REDACTED]"
_PATTERNS = [
    (re.compile(r"eyJ[\w-]+\.[\w-]+\.[\w-]+"), "[REDACTED_JWT]"),
    (re.compile(r"(?i)(bearer\s+)[\w.~+/=-]+"), r"\1" + REDACTED),
    (re.compile(r"(?i)(\"?access_token\"?\s*[:=]\s*\"?)[^\"\s,}]+"), r"\1" + REDACTED),
    (re.compile(r"(?i)(\bsession=)[\w-]+"), r"\1" + REDACTED),
    (re.compile(r"(?i)(\btoken=)[\w-]{8,}"), r"\1" + REDACTED),
    (re.compile(r"(?i)(\"?password\"?\s*[:=]\s*\"?)[^\"\s,}]+"), r"\1" + REDACTED),
    (re.compile(r"\bgsk_[A-Za-z0-9]{10,}"), "[REDACTED_API_KEY]"),
]


def _secrets() -> list[str]:
    values = [u["password"] for u in SEED_USERS]
    key = os.getenv("LLM_API_KEY")
    if key:
        values.append(key)
    return [v for v in values if len(v) >= 6]


def redact_text(text: str) -> str:
    for secret in _secrets():
        text = text.replace(secret, REDACTED)
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def redact(value: Any) -> Any:
    """Redact every string inside a JSON-like structure."""
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()}
    return value


_LOCAL_ORIGIN = re.compile(r"https?://(?:127\.0\.0\.1|localhost):\d+")


def _shorten(value: Any) -> Any:
    """Drop the local origin (http://127.0.0.1:<port>) from URLs; the port changes per run."""
    if isinstance(value, str):
        return _LOCAL_ORIGIN.sub("", value)
    if isinstance(value, list):
        return [_shorten(v) for v in value]
    if isinstance(value, dict):
        return {k: _shorten(v) for k, v in value.items()}
    return value


def _message(error: dict[str, Any]) -> str | None:
    """The error message without Playwright's call log (it is in the traceback already)."""
    message = error.get("message")
    return message.split("\nCall log:", 1)[0] if message else message


def _cut(text: str | None, limit: int, keep_end: bool = False) -> str | None:
    if text is None or len(text) <= limit:
        return text
    return "..." + text[-limit:] if keep_end else text[:limit] + "..."


def _dedupe(lines: list[str]) -> list[str]:
    """Collapse repeated lines into one with a count, keeping first-seen order."""
    counts: dict[str, int] = {}
    for line in lines:
        counts[line] = counts.get(line, 0) + 1
    out = [f"{line} (x{n})" if n > 1 else line for line, n in counts.items()]
    return [_cut(line, MAX_LINE) for line in out][:MAX_LIST_ITEMS]


def _compact_attempt(attempt: dict[str, Any], full: bool) -> dict[str, Any]:
    """Full detail for the first failed attempt; later failed attempts get a short form.

    Reruns usually repeat the same traceback and page state, so sending them in full would
    multiply the payload (about 2.4k characters per attempt) for no new information. What
    differs between attempts (message, location, status, duration) is kept.
    """
    out: dict[str, Any] = {k: attempt[k] for k in ("attempt", "outcome", "duration_s")}
    if attempt["outcome"] == "passed":
        return out
    error = attempt.get("error") or {}
    out["error"] = {
        "phase": error.get("phase"),
        "type": error.get("type"),
        "message": _cut(_message(error), MAX_MESSAGE),
        "location": error.get("location"),
    }
    if full:
        out["error"]["traceback_tail"] = _cut(error.get("traceback_tail"), MAX_TRACEBACK,
                                              keep_end=True)
        out["error"]["log_lines"] = [_cut(line, MAX_LINE) for line in
                                     (error.get("log_lines") or [])[-MAX_LOG_LINES:]]
    if attempt.get("api"):
        api = dict(attempt["api"])
        if full:
            api["body_snippet"] = _cut(api.get("body_snippet"), MAX_BODY)
        else:
            api.pop("body_snippet", None)
        out["api_last_exchange"] = api
    if attempt.get("ui") and full:
        ui = attempt["ui"]
        out["ui"] = {
            "page_url": ui.get("page_url"),
            "console_errors": _dedupe(ui.get("console_errors", [])),
            "failed_requests": _dedupe(ui.get("failed_requests", [])),
        }
    health = attempt.get("health_at_failure")
    out["health_at_failure"] = health if full or not health else {"status": health.get("status")}
    return out


def _compact_attempts(attempts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    first_failed = next(i for i, a in enumerate(attempts) if a["outcome"] != "passed")
    return [_compact_attempt(a, full=i == first_failed) for i, a in enumerate(attempts)]


def group_attempts(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    by_test: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_test[record["nodeid"]].append(record)
    return {k: sorted(v, key=lambda a: a["attempt"]) for k, v in by_test.items()}


def failing_tests(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {nodeid: attempts for nodeid, attempts in group_attempts(records).items()
            if any(a["outcome"] != "passed" for a in attempts)}


def build_tests(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tests = []
    for nodeid, attempts in failing_tests(records).items():
        first = attempts[0]
        tests.append(_shorten(redact({
            "test_id": nodeid,
            "case_id": first.get("case_id"),
            "module": first.get("module"),
            "layer": first.get("layer"),
            "signals": signals.compute(attempts),
            "attempts": _compact_attempts(attempts),
        })))
    return tests


def run_context(records: list[dict[str, Any]], tests: list[dict[str, Any]]) -> dict[str, Any]:
    all_tests = group_attempts(records)
    return {
        "run": {
            "tests_total": len(all_tests),
            "tests_with_a_failed_attempt": len(tests),
            "tests_passed_first_attempt": sum(
                1 for a in all_tests.values() if a[0]["outcome"] == "passed"),
        },
        # One line per failing test: test_id | error category | final outcome | passed on
        # rerun | health ok at failure. Kept terse because it repeats in every chunk.
        "failing_tests_overview": [
            f"{t['test_id']} | {t['signals']['error_category_heuristic']}"
            f" | final={t['signals']['final_outcome']}"
            f" | passed_on_rerun={t['signals']['passed_on_rerun']}"
            f" | health_ok={t['signals']['health_ok_at_failure']}"
            for t in tests
        ],
    }


def chunk(tests: list[dict[str, Any]], budget_chars: int = DEFAULT_CHUNK_CHARS
          ) -> list[list[dict[str, Any]]]:
    """Greedy packing by serialised size. A test larger than the budget gets its own chunk."""
    chunks: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    size = 0
    for test in tests:
        test_size = len(json.dumps(test))
        if current and size + test_size > budget_chars:
            chunks.append(current)
            current, size = [], 0
        current.append(test)
        size += test_size
    if current:
        chunks.append(current)
    return chunks


def build_payloads(records: list[dict[str, Any]], budget_chars: int = DEFAULT_CHUNK_CHARS
                   ) -> list[dict[str, Any]]:
    """One payload per LLM call. Each contains the run context and its share of the tests."""
    tests = build_tests(records)
    context = run_context(records, tests)
    chunks = chunk(tests, budget_chars)
    return [
        {**context, "chunk": {"index": i + 1, "of": len(chunks)}, "tests": part}
        for i, part in enumerate(chunks)
    ]
