"""CLI: copy one real classified run into samples/ and screenshot the report section.

  python -m scripts.export_samples --run <run-id>

Copies classification.json, classification.md and the self-contained report.html, takes
screenshots of the LLM section in the HTML report, and writes a README stamped with the model,
prompt version and timestamps. Only real runs are exported; nothing is edited.
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
SAMPLES = ROOT / "samples"


def screenshots(report_html: Path, out: Path) -> list[str]:
    taken = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 1000})
        page.goto(report_html.resolve().as_uri())
        summary = page.locator(".testmu-llm-summary")
        summary.wait_for()
        summary.screenshot(path=out / "report-llm-summary.png")
        taken.append("report-llm-summary.png")

        # pytest-html expands failed rows by default; expand only if it is collapsed.
        row = page.locator("tbody.failed").first
        block = row.locator(".testmu-llm-classification")
        block.wait_for(state="attached")
        if not block.is_visible():
            row.locator(".collapsible td").first.click()
        block.wait_for()
        row.screenshot(path=out / "report-test-classification.png")
        taken.append("report-test-classification.png")
        browser.close()
    return taken


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", required=True, help="run id, e.g. eval-<stamp>-mixed")
    args = parser.parse_args()

    run_dir = REPORTS / f"run-{args.run}"
    classification = run_dir / "classification.json"
    if not classification.exists():
        print(f"error: {classification} not found; classify the run first", file=sys.stderr)
        return 2
    report = json.loads(classification.read_text(encoding="utf-8"))
    meta = json.loads((run_dir / "run-meta.json").read_text(encoding="utf-8"))

    out = SAMPLES / args.run
    out.mkdir(parents=True, exist_ok=True)
    for name in ("classification.json", "classification.md", "report.html", "run-meta.json"):
        shutil.copy(run_dir / name, out / name)
    taken = screenshots(out / "report.html", out)

    s = report["run_summary"]
    (out / "README.md").write_text("\n".join([
        f"# Sample: classified run `{args.run}`",
        "",
        "Real output, copied unchanged from `reports/` by `scripts/export_samples.py`.",
        "",
        f"- Model: `{report['model']}` ({report['provider']}), temperature"
        f" {report['temperature']}, prompt `classifier.{report['prompt_version']}`",
        f"- Classified at: {report['generated_at_utc']}",
        f"- Tests: {s['total']}; with a failed attempt: {s['failed']}; by bucket: {s['by_bucket']}",
        f"- Faults injected (ground truth, never sent to the LLM):"
        f" {', '.join(meta['active_faults_for_evaluation_only']) or 'none'}",
        f"- Reruns: {meta['reruns']}; git SHA: `{meta['git_sha']}`",
        "",
        "Files:",
        "- `report.html`: the pytest-html report with the LLM classification inside it"
        " (summary above the results, an \"LLM bucket\" column, and a block per failing test)",
        "- `classification.json` / `classification.md`: the classifier's output",
        *[f"- `{name}`: screenshot of the report" for name in taken],
        "",
    ]), encoding="utf-8", newline="\n")
    print(f"Exported {args.run} to {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
