"""Renders classification.md and injects results into the pytest-html report.

The HTML report gets:
- a run-level summary above the results table (counts per bucket, model, prompt version);
- an "LLM bucket" column for every test;
- a per-test block with bucket, confidence, evidence, reasoning and next action.

Run summary uses pytest-html's documented summary lists. The per-test parts edit the row data
pytest-html keeps until it writes the file at session end; that data structure is internal
to pytest-html, so the version is pinned (4.2.0) in requirements.txt.
"""

import html
from typing import TYPE_CHECKING

import pytest
from pytest_html import extras
from pytest_html.basereport import BaseReport

if TYPE_CHECKING:
    from ai.classifier.classify import Classification, ClassificationReport

BUCKET_ORDER = ["real_bug", "environment_issue", "flaky", "unclassified"]
BUCKET_TITLES = {
    "real_bug": "Real bugs",
    "environment_issue": "Environment issues",
    "flaky": "Flaky tests",
    "unclassified": "Unclassified (no valid LLM answer)",
}
PLACEHOLDER_CELL = '<td class="col-llm-bucket">—</td>'
_ENABLED_KEY = pytest.StashKey[bool]()


def _cell(text: str) -> str:
    return html.escape(text).replace("|", "\\|").replace("\n", " ")


def render_markdown(report: "ClassificationReport") -> str:
    s = report.run_summary
    counts = ", ".join(f"{b}: {s.by_bucket.get(b, 0)}" for b in BUCKET_ORDER if b in s.by_bucket)
    lines = [
        f"# Failure classification: run {report.run_id}",
        "",
        f"- Model: `{report.model}` ({report.provider}), temperature {report.temperature},"
        f" prompt `classifier.{report.prompt_version}` (SHA-256 `{report.prompt_sha256[:12]}…`)",
        f"- Generated: {report.generated_at_utc}",
        f"- Tests: {s.total}; with a failed attempt: {s.failed}; {counts or 'nothing to classify'}",
        f"- LLM calls: {len(report.llm_calls)}"
        f" ({sum(c.attempts for c in report.llm_calls)} requests including retries)",
        "",
    ]
    for bucket in BUCKET_ORDER:
        items = [c for c in report.classifications if c.bucket == bucket]
        if not items:
            continue
        lines += [
            f"## {BUCKET_TITLES[bucket]} ({len(items)})",
            "",
            "| Test | Case | Confidence | Final outcome | Reasoning | Next action |",
            "|---|---|---|---|---|---|",
        ]
        for c in items:
            confidence = f"{c.confidence:.2f}" if c.confidence is not None else "—"
            outcome = f"{c.final_outcome} ({c.failed_attempts}/{c.attempts} attempts failed)"
            lines.append(f"| `{c.test_id}` | {c.case_id or '—'} | {confidence} | {outcome} |"
                         f" {_cell(c.reasoning)} | {_cell(c.suggested_next_action)} |")
        lines.append("")
        lines += ["Evidence:", ""]
        for c in items:
            lines.append(f"- `{c.test_id}`")
            lines += [f"  - `{_cell(e)}`" for e in c.evidence]
        lines.append("")
    failed_calls = [c for c in report.llm_calls if not c.valid]
    if failed_calls:
        lines += ["## LLM call problems", ""]
        for call in failed_calls:
            lines += [f"- chunk {call.chunk}: " + "; ".join(call.errors)[:500]]
        lines.append("")
    return "\n".join(lines)


def _summary_html(report: "ClassificationReport") -> str:
    s = report.run_summary
    counts = "".join(
        f"<li><strong>{BUCKET_TITLES[b]}</strong>: {s.by_bucket[b]}</li>"
        for b in BUCKET_ORDER if b in s.by_bucket
    )
    rows = "".join(
        f"<tr><td>{html.escape(c.test_id)}</td><td>{html.escape(c.bucket)}</td>"
        f"<td>{'' if c.confidence is None else f'{c.confidence:.2f}'}</td>"
        f"<td>{html.escape(c.reasoning)}</td></tr>"
        for c in report.classifications
    )
    return (
        "<div class='testmu-llm-summary'>"
        "<h2>LLM failure classification (Flaky Test Classifier)</h2>"
        f"<p>{s.failed} of {s.total} tests had a failed attempt. Model "
        f"<code>{html.escape(report.model)}</code>, prompt "
        f"<code>classifier.{html.escape(report.prompt_version)}</code>, generated "
        f"{html.escape(report.generated_at_utc)}.</p>"
        f"<ul>{counts}</ul>"
        "<table><thead><tr><th>Test</th><th>Bucket</th><th>Confidence</th><th>Reasoning</th>"
        f"</tr></thead><tbody>{rows}</tbody></table></div>"
    )


def _test_html(c: "Classification") -> str:
    evidence = "".join(f"<li><code>{html.escape(e)}</code></li>" for e in c.evidence)
    confidence = "—" if c.confidence is None else f"{c.confidence:.2f}"
    return (
        "<div class='testmu-llm-classification'><h4>LLM classification</h4>"
        f"<p><strong>{html.escape(c.bucket)}</strong> (confidence {confidence})</p>"
        f"<p>{html.escape(c.reasoning)}</p>"
        f"<p><em>Next action:</em> {html.escape(c.suggested_next_action)}</p>"
        f"<ul>{evidence}</ul></div>"
    )


def _html_plugin(config: pytest.Config) -> BaseReport | None:
    return next((p for p in config.pluginmanager.get_plugins() if isinstance(p, BaseReport)),
                None)


def attach_to_html_report(config: pytest.Config, report: "ClassificationReport") -> None:
    plugin = _html_plugin(config)
    if plugin is None:
        return
    plugin._report.additional_summary["prefix"].append(_summary_html(report))
    tests = plugin._report._data["tests"]
    for c in report.classifications:
        cell = f'<td class="col-llm-bucket">{html.escape(c.bucket)}</td>'
        for entry in tests.get(c.test_id, []):
            entry["extras"] = [*entry.get("extras", []), extras.html(_test_html(c))]
            entry["resultsTableRow"] = [cell if r == PLACEHOLDER_CELL else r
                                        for r in entry["resultsTableRow"]]


# --- pytest-html column hooks (registered through ai.classifier.collector) ---------------------

def classification_enabled(config: pytest.Config) -> bool:
    return config.stash.get(_ENABLED_KEY, False)


def enable_column(config: pytest.Config, enabled: bool) -> None:
    config.stash[_ENABLED_KEY] = enabled


def add_header(config: pytest.Config, cells: list[str]) -> None:
    if classification_enabled(config):
        cells.insert(2, '<th class="col-llm-bucket">LLM bucket</th>')


def add_row(config: pytest.Config, cells: list[str]) -> None:
    if classification_enabled(config):
        cells.insert(2, PLACEHOLDER_CELL)
