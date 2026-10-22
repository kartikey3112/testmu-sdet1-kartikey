"""Sends a versioned prompt file to the LLM and stores the verbatim response with metadata.

The prompt file is sent unchanged as a single user message, at temperature 0. The raw
response is saved before anything else happens to it, so a parsing or validation bug can
never lose what the model actually said.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from ai.llm_client import chat, load_llm_config
from ai.testgen.validators import ValidationReport, render_markdown, validate_text

ROOT = Path(__file__).resolve().parents[2]
PROMPTS_DIR = ROOT / "prompts"
RAW_DIR = ROOT / "generated" / "raw"
TEMPERATURE = 0
# Groq applies a low default output cap; gpt-oss also spends part of the budget on hidden
# reasoning. Without this, v1 Login was cut off at 3072 tokens (finish_reason=length).
MAX_COMPLETION_TOKENS = 16384


@dataclass
class GenerationResult:
    raw_path: Path
    report_path: Path
    report: ValidationReport


def prompt_path(module: str, version: str) -> Path:
    return PROMPTS_DIR / f"{module}.{version}.md"


def generate(module: str, version: str) -> GenerationResult:
    path = prompt_path(module, version)
    prompt_bytes = path.read_bytes()
    config = load_llm_config()

    result = chat(
        [{"role": "user", "content": prompt_bytes.decode("utf-8")}],
        config=config, temperature=TEMPERATURE, json_mode=True,
        extra={"max_completion_tokens": MAX_COMPLETION_TOKENS},
    )

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    stem = f"{module}.{version}.{timestamp}"
    record = {
        "metadata": {
            "module": module,
            "prompt_version": version,
            "prompt_file": path.relative_to(ROOT).as_posix(),
            "prompt_sha256": hashlib.sha256(prompt_bytes).hexdigest(),
            "provider": config.provider,
            "base_url": config.base_url,
            "model_requested": config.model,
            "model_reported": result.model,
            "temperature": TEMPERATURE,
            "response_format": "json_object",
            "max_completion_tokens": MAX_COMPLETION_TOKENS,
            "finish_reason": result.finish_reason,
            "timestamp_utc": timestamp,
            "latency_s": result.latency_s,
            "attempts": result.attempts,
            "usage": result.usage,
        },
        "content": result.content,
        "api_response": result.raw,
    }
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RAW_DIR / f"{stem}.json"
    raw_path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    report, _ = validate_text(module, result.content, finish_reason=result.finish_reason)
    report_path = write_report(report, raw_path)
    return GenerationResult(raw_path=raw_path, report_path=report_path, report=report)


def write_report(report: ValidationReport, raw_path: Path) -> Path:
    stem = raw_path.name.removesuffix(".json")
    report_path = raw_path.with_name(f"{stem}.report.md")
    report_path.write_text(render_markdown(report, stem), encoding="utf-8")
    raw_path.with_name(f"{stem}.report.json").write_text(
        json.dumps(report.to_dict(), indent=2) + "\n", encoding="utf-8"
    )
    return report_path


def revalidate(raw_path: Path) -> GenerationResult:
    """Re-run validation on a saved raw response without calling the LLM."""
    record = json.loads(raw_path.read_text(encoding="utf-8"))
    module = record["metadata"]["module"]
    finish_reason = record["api_response"]["choices"][0].get("finish_reason")
    report, _ = validate_text(module, record["content"], finish_reason=finish_reason)
    return GenerationResult(raw_path=raw_path, report_path=write_report(report, raw_path),
                            report=report)
