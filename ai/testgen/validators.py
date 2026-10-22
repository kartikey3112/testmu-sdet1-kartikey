"""Validation report: schema errors, coverage matrix, duplicates, non-checkable expectations.

Everything here is deterministic code. The report is what each prompt revision must point to
("v2 fixes X, seen in the v1 report").
"""

import json
import re
from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher
from typing import Any

from jsonschema import Draft202012Validator

from ai.testgen.schema import COVERAGE_AREAS, case_schema
from app.seed import SEED_USERS

NEAR_DUPLICATE_RATIO = 0.85
CASE_COUNT_RANGE = (15, 25)
NEGATIVE_LIKE = {"negative", "boundary", "security"}

VAGUE_PHRASES = [
    r"works? (correctly|properly|fine|as intended)",
    r"as expected",
    r"\bappropriate(ly)?\b",
    r"\bproperly\b",
    r"\bcorrect(ly)? (error|message|behaviou?r|response)\b",
    r"\bshould (work|succeed|fail)\b",
    r"\bvalid response\b",
    r"\bsome (error|message)\b",
]
# Models often swap ASCII "-" and quotes for typographic ones. Inside an "exact" message that
# makes the expected string differ from what the app renders (seen in Login v1: U+2011).
TYPOGRAPHIC = re.compile("[‐-―‘’“”]")

VAGUE = re.compile("|".join(VAGUE_PHRASES), re.IGNORECASE)


@dataclass
class ValidationReport:
    module: str
    truncated: bool = False
    json_error: str | None = None
    schema_errors: list[str] = field(default_factory=list)
    case_count: int = 0
    case_count_ok: bool = False
    coverage: dict[str, dict[str, Any]] = field(default_factory=dict)
    coverage_gaps: list[str] = field(default_factory=list)
    coverage_map_issues: list[str] = field(default_factory=list)
    id_issues: list[str] = field(default_factory=list)
    duplicate_titles: list[str] = field(default_factory=list)
    vague_expectations: list[str] = field(default_factory=list)
    hardcoded_credentials: list[str] = field(default_factory=list)
    typographic_characters: list[str] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)
    automation_candidates: int = 0

    @property
    def passed(self) -> bool:
        return not (
            self.truncated or self.json_error or self.schema_errors or not self.case_count_ok
            or self.coverage_gaps or self.coverage_map_issues or self.id_issues
            or self.duplicate_titles or self.vague_expectations or self.hardcoded_credentials
            or self.typographic_characters
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"passed": self.passed}


def validate_text(
    module: str, text: str, finish_reason: str | None = None
) -> tuple[ValidationReport, dict[str, Any] | None]:
    report = ValidationReport(module=module, truncated=finish_reason == "length")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        report.json_error = f"Response is not valid JSON: {exc}"
        return report, None
    validate_data(module, data, report)
    return report, data


def validate_data(module: str, data: Any, report: ValidationReport) -> ValidationReport:
    validator = Draft202012Validator(case_schema(module))
    report.schema_errors = [
        f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
        for e in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    ]
    if not isinstance(data, dict):
        return report

    cases = [c for c in data.get("cases", []) if isinstance(c, dict)]
    report.case_count = len(cases)
    report.case_count_ok = CASE_COUNT_RANGE[0] <= len(cases) <= CASE_COUNT_RANGE[1]
    report.open_questions = [q for q in data.get("open_questions", []) if isinstance(q, str)]
    report.automation_candidates = sum(1 for c in cases if c.get("automation_candidate") is True)

    _check_ids(cases, report)
    _check_coverage(module, cases, data.get("coverage_map"), report)
    _check_duplicates(cases, report)
    _check_expectations(cases, report)
    _check_credentials(data, report)
    _check_typography(cases, report)
    return report


def _check_ids(cases: list[dict], report: ValidationReport) -> None:
    ids = [c.get("id") for c in cases]
    seen = set()
    for case_id in ids:
        if case_id in seen:
            report.id_issues.append(f"duplicate id {case_id}")
        seen.add(case_id)
    numbers = [
        int(i.split("-")[1]) for i in ids
        if isinstance(i, str) and re.fullmatch(r"\w+-\d{3}", i)
    ]
    if numbers and numbers != list(range(1, len(numbers) + 1)):
        report.id_issues.append(f"ids are not sequential from 001: {ids}")


def _check_coverage(module: str, cases: list[dict], coverage_map: Any,
                    report: ValidationReport) -> None:
    by_id = {c.get("id"): c for c in cases}
    for area in COVERAGE_AREAS[module]:
        in_area = [c for c in cases if c.get("coverage_area") == area]
        positive = [c["id"] for c in in_area if c.get("type") == "positive"]
        negative = [c["id"] for c in in_area if c.get("type") in NEGATIVE_LIKE]
        report.coverage[area] = {
            "cases": [c.get("id") for c in in_area],
            "positive": len(positive),
            "negative_boundary_security": len(negative),
        }
        if not positive:
            report.coverage_gaps.append(f"'{area}' has no positive case")
        if not negative:
            report.coverage_gaps.append(f"'{area}' has no negative/boundary/security case")

    if not isinstance(coverage_map, dict):
        return
    for area, ids in coverage_map.items():
        for case_id in ids if isinstance(ids, list) else []:
            case = by_id.get(case_id)
            if case is None:
                report.coverage_map_issues.append(f"coverage_map['{area}'] lists unknown {case_id}")
            elif case.get("coverage_area") != area:
                report.coverage_map_issues.append(
                    f"coverage_map['{area}'] lists {case_id}, whose coverage_area is "
                    f"'{case.get('coverage_area')}'"
                )
    for case in cases:
        area = case.get("coverage_area")
        if area in coverage_map and case.get("id") not in coverage_map.get(area, []):
            report.coverage_map_issues.append(
                f"{case.get('id')} missing from coverage_map['{area}']"
            )


def _normalise(title: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", title.lower()).strip()


def _check_duplicates(cases: list[dict], report: ValidationReport) -> None:
    titled = [(c.get("id"), _normalise(str(c.get("title", "")))) for c in cases]
    for i, (id_a, a) in enumerate(titled):
        for id_b, b in titled[i + 1:]:
            ratio = SequenceMatcher(None, a, b).ratio()
            if ratio >= NEAR_DUPLICATE_RATIO:
                kind = "duplicate" if a == b else f"near-duplicate ({ratio:.2f})"
                report.duplicate_titles.append(f"{id_a} / {id_b}: {kind}")


def _check_expectations(cases: list[dict], report: ValidationReport) -> None:
    for case in cases:
        for result in case.get("expected_results", []):
            if isinstance(result, str) and VAGUE.search(result):
                report.vague_expectations.append(f"{case.get('id')}: {result}")


def _check_typography(cases: list[dict], report: ValidationReport) -> None:
    for case in cases:
        fields = [*case.get("expected_results", []), json.dumps(case.get("test_data", {}),
                                                              ensure_ascii=False)]
        hits = sorted({f"U+{ord(ch):04X}" for text in fields if isinstance(text, str)
                       for ch in TYPOGRAPHIC.findall(text)})
        if hits:
            report.typographic_characters.append(f"{case.get('id')}: {', '.join(hits)}")


def _check_credentials(data: dict, report: ValidationReport) -> None:
    text = json.dumps(data)
    for user in SEED_USERS:
        if user["password"] in text:
            report.hardcoded_credentials.append(
                f"real password of {user['email']} appears instead of a placeholder"
            )


def render_markdown(report: ValidationReport, title: str) -> str:
    result = "PASS" if report.passed else "FAIL"
    lines = [f"# Validation report: {title}", "", f"**Result: {result}**", ""]
    if report.truncated:
        lines += ["- **Truncated:** output hit the token limit (finish_reason=length)", ""]
    if report.json_error:
        return "\n".join(lines + [f"- JSON error: {report.json_error}", ""])

    lines += [
        f"- Cases: {report.case_count} (expected {CASE_COUNT_RANGE[0]}–{CASE_COUNT_RANGE[1]})"
        f"{'' if report.case_count_ok else ' ← out of range'}",
        f"- Automation candidates: {report.automation_candidates}",
        f"- Open questions: {len(report.open_questions)}",
        "",
        "## Coverage matrix",
        "",
        "| Required area | Cases | Positive | Negative / boundary / security |",
        "|---|---|---|---|",
    ]
    for area, row in report.coverage.items():
        lines.append(f"| {area} | {', '.join(row['cases']) or '—'} | {row['positive']} | "
                     f"{row['negative_boundary_security']} |")
    sections = [
        ("Schema errors", report.schema_errors),
        ("Coverage gaps", report.coverage_gaps),
        ("coverage_map mismatches", report.coverage_map_issues),
        ("ID issues", report.id_issues),
        ("Duplicate or near-duplicate titles", report.duplicate_titles),
        ("Non-checkable expected results", report.vague_expectations),
        ("Hard-coded credentials", report.hardcoded_credentials),
        ("Typographic characters in exact strings", report.typographic_characters),
        ("Open questions from the model", report.open_questions),
    ]
    for heading, items in sections:
        lines += ["", f"## {heading}", ""]
        lines += [f"- {item}" for item in items] if items else ["None."]
    return "\n".join(lines) + "\n"
