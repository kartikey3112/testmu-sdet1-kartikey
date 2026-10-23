"""Calls the LLM, validates the structured response, retries once, writes outputs.

  python -m ai.classifier.classify --run <run-id>      # or: make classify RUN=<run-id>

Reads reports/run-<id>/execution-log.jsonl and writes classification.json and
classification.md next to it. The LLM call is real: there is no mock or canned response
anywhere in this path. Without LLM_API_KEY it stops with a message and writes nothing.

Reliability rules:
- The response must be JSON matching LLMResponse, contain every test in the chunk exactly
  once, and cite only evidence fields that exist in that test's payload.
- On any violation, retry once with the validation errors included.
- Whatever is still invalid becomes `unclassified`. The classifier never guesses.
- Rate limits (429, and Groq's 413 per-minute window) are retried with backoff in llm_client.
"""

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from ai.classifier import payload as payload_builder
from ai.llm_client import (
    ChatResult,
    LLMConfigError,
    LLMError,
    LLMInvalidJSONError,
    LLMQuotaError,
    chat,
    load_llm_config,
)

ROOT = Path(__file__).resolve().parents[2]
PROMPTS_DIR = ROOT / "prompts"
PROMPT_VERSION = "v1"
MAX_COMPLETION_TOKENS = 4096
TEMPERATURE = 0

Bucket = Literal["real_bug", "environment_issue", "flaky"]
EVIDENCE_PATH = re.compile(r"^\s*`?(?P<path>[A-Za-z_][\w]*(?:\[\d+\]|\.[A-Za-z_]\w*)*)`?\s*:")


# --- Schemas -----------------------------------------------------------------------------------

class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LLMClassification(Strict):
    test_id: str
    case_id: str | None
    bucket: Bucket
    confidence: float = Field(ge=0, le=1)
    evidence: list[str] = Field(min_length=1, max_length=4)
    reasoning: str
    suggested_next_action: str = Field(min_length=1)

    @field_validator("reasoning")
    @classmethod
    def _at_most_three_sentences(cls, value: str) -> str:
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", value.strip()) if s]
        if len(sentences) > 3:
            raise ValueError(f"reasoning has {len(sentences)} sentences; at most 3 allowed")
        return value


class LLMResponse(Strict):
    classifications: list[LLMClassification]


class Classification(Strict):
    test_id: str
    case_id: str | None
    bucket: Literal["real_bug", "environment_issue", "flaky", "unclassified"]
    confidence: float | None
    evidence: list[str]
    reasoning: str
    suggested_next_action: str
    final_outcome: str
    failed_attempts: int
    attempts: int


class RunSummary(Strict):
    total: int
    failed: int
    by_bucket: dict[str, int]


class LLMCall(Strict):
    chunk: int
    tests: int
    attempts: int
    valid: bool
    latency_s: float
    finish_reason: str | None
    usage: dict[str, Any]
    errors: list[str]


class ClassificationReport(Strict):
    run_id: str
    generated_at_utc: str
    provider: str
    model: str
    prompt_version: str
    prompt_sha256: str
    temperature: float
    run_summary: RunSummary
    classifications: list[Classification]
    llm_calls: list[LLMCall]


# --- Validation --------------------------------------------------------------------------------

def _resolve(data: Any, path: str) -> bool:
    """True if a path like attempts[1].error.message exists in data."""
    current = data
    for name, index in re.findall(r"([A-Za-z_]\w*)|\[(\d+)\]", path):
        if name:
            if not isinstance(current, dict) or name not in current:
                return False
            current = current[name]
        else:
            if not isinstance(current, list) or int(index) >= len(current):
                return False
            current = current[int(index)]
    return True


Problem = tuple[str | None, str]  # (test_id it concerns, or None for the whole response; text)


def validate_response(text: str, tests: list[dict[str, Any]]
                      ) -> tuple[dict[str, LLMClassification], list[Problem]]:
    """Return the valid classifications by test_id and the problems found."""
    try:
        parsed = LLMResponse.model_validate_json(text)
    except ValidationError as exc:
        return {}, [(None, f"schema: {e['loc']}: {e['msg']}") for e in exc.errors()[:10]]

    expected = {t["test_id"]: t for t in tests}
    valid: dict[str, LLMClassification] = {}
    problems: list[Problem] = []
    seen: Counter[str] = Counter(c.test_id for c in parsed.classifications)
    for item in parsed.classifications:
        test = expected.get(item.test_id)
        if test is None:
            problems.append((None, f"{item.test_id}: not a test in this request"))
            continue
        if seen[item.test_id] > 1:
            problems.append((item.test_id, "classified more than once"))
            continue
        if item.case_id != test.get("case_id"):
            problems.append((item.test_id, f"case_id must be {test.get('case_id')!r}"))
            continue
        bad = []
        for evidence in item.evidence:
            match = EVIDENCE_PATH.match(evidence)
            if not match or not _resolve(test, match["path"]):
                bad.append(evidence[:80])
        if bad:
            problems.append((item.test_id, f"evidence does not cite a field in its data: {bad}"))
            continue
        valid[item.test_id] = item
    mentioned = {test_id for test_id, _ in problems}
    for test_id in sorted(expected.keys() - valid.keys() - mentioned):
        problems.append((test_id, "missing from the response"))
    return valid, problems


def describe(problems: list[Problem]) -> list[str]:
    return [f"{test_id}: {text}" if test_id else text for test_id, text in problems]


# --- Classification ----------------------------------------------------------------------------

ChatFn = Callable[..., ChatResult]


def load_prompt(version: str = PROMPT_VERSION) -> tuple[str, str]:
    path = PROMPTS_DIR / f"classifier.{version}.md"
    raw = path.read_bytes()
    return raw.decode("utf-8"), hashlib.sha256(raw).hexdigest()


def classify_chunk(system_prompt: str, request: dict[str, Any], chunk_index: int,
                   chat_fn: ChatFn = chat, **chat_kwargs: Any
                   ) -> tuple[dict[str, LLMClassification], LLMCall]:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(request, ensure_ascii=False)},
    ]
    tests = request["tests"]
    extra = {"max_completion_tokens": MAX_COMPLETION_TOKENS}

    def ask(msgs: list[dict[str, str]]) -> ChatResult:
        try:
            return chat_fn(msgs, temperature=TEMPERATURE, json_mode=True, extra=extra,
                           **chat_kwargs)
        except LLMInvalidJSONError as exc:
            # The provider rejected the model's JSON itself. Treat what the model wrote like
            # any other invalid answer, so it gets the same single retry.
            return ChatResult(content=exc.failed_generation, model="", usage={}, raw={},
                              attempts=1, latency_s=0.0, finish_reason="json_validate_failed")

    result = ask(messages)
    valid, problems = validate_response(result.content, tests)
    attempts, latency, usage = 1, result.latency_s, dict(result.usage)
    finish_reason = result.finish_reason

    if problems:
        # One retry, telling the model exactly what was wrong.
        retry_messages = messages + [
            {"role": "assistant", "content": result.content},
            {"role": "user", "content": "Your response was invalid:\n- "
                + "\n- ".join(describe(problems))
                + "\nReturn the complete corrected JSON object for all tests, and nothing else."},
        ]
        retry = ask(retry_messages)
        retry_valid, retry_problems = validate_response(retry.content, tests)
        valid = {**valid, **retry_valid}
        problems = [p for p in retry_problems if p[0] not in valid]
        attempts, latency = 2, round(latency + retry.latency_s, 2)
        usage = {"first": usage, "retry": dict(retry.usage)}
        finish_reason = retry.finish_reason

    call = LLMCall(chunk=chunk_index, tests=len(tests), attempts=attempts, valid=not problems,
                   latency_s=latency, finish_reason=finish_reason, usage=usage,
                   errors=describe(problems))
    return valid, call


def load_records(run_dir: Path) -> list[dict[str, Any]]:
    log = run_dir / "execution-log.jsonl"
    with log.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def classify_run(run_dir: Path, chat_fn: ChatFn = chat, prompt_version: str = PROMPT_VERSION,
                 budget_chars: int = payload_builder.DEFAULT_CHUNK_CHARS,
                 raise_on_quota: bool = False) -> ClassificationReport:
    """Classify every failing test in a run and write classification.json / .md.

    If the provider's quota runs out (LLMQuotaError), the remaining chunks are not attempted:
    their tests are written as `unclassified` with the reason, or, with raise_on_quota, the
    error is raised and nothing is written (the evaluation uses that, so it never scores a
    run that could not be classified).
    """
    config = load_llm_config()  # raises LLMConfigError before anything is written
    system_prompt, prompt_sha = load_prompt(prompt_version)
    records = load_records(run_dir)
    requests = payload_builder.build_payloads(records, budget_chars)
    failing = payload_builder.failing_tests(records)

    results: dict[str, LLMClassification] = {}
    calls: list[LLMCall] = []
    not_sent: set[str] = set()
    for i, request in enumerate(requests, start=1):
        try:
            valid, call = classify_chunk(system_prompt, request, i, chat_fn, config=config)
        except LLMQuotaError as exc:
            if raise_on_quota:
                raise
            calls.append(LLMCall(chunk=i, tests=len(request["tests"]), attempts=0, valid=False,
                                 latency_s=0, finish_reason=None, usage={},
                                 errors=[f"quota exhausted; chunks {i}-{len(requests)} not sent:"
                                         f" {str(exc)[:300]}"]))
            not_sent = {t["test_id"] for r in requests[i - 1:] for t in r["tests"]}
            break
        except LLMError as exc:
            call = LLMCall(chunk=i, tests=len(request["tests"]), attempts=0, valid=False,
                           latency_s=0, finish_reason=None, usage={}, errors=[str(exc)[:300]])
            valid = {}
        results.update(valid)
        calls.append(call)

    classifications = []
    for test_id, attempts in failing.items():
        final = attempts[-1]["outcome"]
        failed_count = sum(1 for a in attempts if a["outcome"] != "passed")
        item = results.get(test_id)
        if item is None:
            classifications.append(Classification(
                test_id=test_id, case_id=attempts[0].get("case_id"), bucket="unclassified",
                confidence=None, evidence=[],
                reasoning=("Not sent: the LLM quota ran out before this test's chunk."
                           if test_id in not_sent
                           else "No valid classification after one retry."),
                suggested_next_action="Triage manually.", final_outcome=final,
                failed_attempts=failed_count, attempts=len(attempts)))
        else:
            classifications.append(Classification(
                **item.model_dump(), final_outcome=final, failed_attempts=failed_count,
                attempts=len(attempts)))

    all_tests = payload_builder.group_attempts(records)
    report = ClassificationReport(
        run_id=run_dir.name.removeprefix("run-"),
        generated_at_utc=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        provider=config.provider,
        model=config.model,
        prompt_version=prompt_version,
        prompt_sha256=prompt_sha,
        temperature=TEMPERATURE,
        run_summary=RunSummary(
            total=len(all_tests), failed=len(failing),
            by_bucket=dict(Counter(c.bucket for c in classifications))),
        classifications=classifications,
        llm_calls=calls,
    )
    write_outputs(run_dir, report)
    return report


def write_outputs(run_dir: Path, report: ClassificationReport) -> None:
    from ai.classifier.report import render_markdown

    (run_dir / "classification.json").write_text(
        report.model_dump_json(indent=2) + "\n", encoding="utf-8", newline="\n")
    (run_dir / "classification.md").write_text(
        render_markdown(report), encoding="utf-8", newline="\n")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Classify the failures of a test run.")
    parser.add_argument("--run", help="run id (default: the latest run)")
    parser.add_argument("--prompt-version", default=PROMPT_VERSION)
    args = parser.parse_args()
    run_id = args.run or (ROOT / "reports" / "latest-run.txt").read_text(encoding="utf-8").strip()
    run_dir = ROOT / "reports" / f"run-{run_id}"
    if not (run_dir / "execution-log.jsonl").exists():
        print(f"error: no execution log in {run_dir}", file=sys.stderr)
        return 2
    try:
        report = classify_run(run_dir, prompt_version=args.prompt_version)
    except LLMConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"{report.run_summary.failed} failing of {report.run_summary.total} tests: "
          f"{report.run_summary.by_bucket}")
    print(f"Wrote {run_dir / 'classification.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
