"""Exports accepted JSON test cases to Gherkin .feature files.

One feature per module; one Rule per required coverage area; one Scenario per case.
preconditions -> Given, steps -> When, expected_results -> Then. Case ID, priority and type
become tags, so a scenario can be traced back to generated/<module>.json and to its test.

  python -m ai.testgen.to_gherkin            # all modules with an accepted file
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

from ai.testgen.accept import GENERATED_DIR
from ai.testgen.schema import COVERAGE_AREAS

GHERKIN_DIR = GENERATED_DIR / "gherkin"
FEATURE_NAMES = {"login": "Login", "dashboard": "Dashboard", "api": "REST API"}


def _line(text: str) -> str:
    # A Gherkin step is one line; collapse any line breaks the model put inside a string.
    return re.sub(r"\s+", " ", str(text)).strip()


def _tag(text: str) -> str:
    return "@" + re.sub(r"[^\w-]+", "_", text.strip())


def _block(keyword: str, items: list[str]) -> list[str]:
    return [f"      {keyword if i == 0 else 'And'} {_line(item)}" for i, item in enumerate(items)]


def scenario(case: dict[str, Any]) -> list[str]:
    tags = [_tag(case["id"]), _tag(case["priority"]), _tag(case["type"])]
    if case.get("automation_candidate"):
        tags.append("@automation_candidate")
    lines = [f"    {' '.join(tags)}", f"    Scenario: {case['id']} {_line(case['title'])}"]
    if case.get("test_data"):
        lines.append(f"      # test_data: {json.dumps(case['test_data'], ensure_ascii=False)}")
    if case.get("notes"):
        lines.append(f"      # notes: {_line(case['notes'])}")
    lines += _block("Given", case.get("preconditions") or ["the app has been reset to seed data"])
    lines += _block("When", case["steps"])
    lines += _block("Then", case["expected_results"])
    return lines


def to_feature(module: str, data: dict[str, Any], source: str) -> str:
    lines = [
        f"# Generated from {source} by ai/testgen/to_gherkin.py. Do not edit by hand.",
        f"@{module}",
        f"Feature: {FEATURE_NAMES[module]} regression cases",
    ]
    for question in data.get("open_questions", []):
        lines.append(f"  # Open question from generation: {_line(question)}")
    for area in COVERAGE_AREAS[module]:
        cases = [c for c in data["cases"] if c.get("coverage_area") == area]
        if not cases:
            continue
        lines += ["", f"  Rule: {area}"]
        for case in cases:
            lines += [""] + scenario(case)
    return "\n".join(lines) + "\n"


def export(module: str) -> Path:
    source = GENERATED_DIR / f"{module}.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    GHERKIN_DIR.mkdir(parents=True, exist_ok=True)
    out = GHERKIN_DIR / f"{module}.feature"
    out.write_text(to_feature(module, data, f"generated/{module}.json"), encoding="utf-8",
                   newline="\n")
    return out


def main() -> int:
    modules = [m for m in COVERAGE_AREAS if (GENERATED_DIR / f"{m}.json").exists()]
    for module in modules:
        print(f"{module}: {export(module).relative_to(GENERATED_DIR.parent).as_posix()}")
    return 0 if modules else 1


if __name__ == "__main__":
    sys.exit(main())
