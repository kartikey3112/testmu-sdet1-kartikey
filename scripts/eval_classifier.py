"""CLI: run fault scenarios, classify failures and score against ground truth.

  python -m scripts.eval_classifier                    # all scenarios
  python -m scripts.eval_classifier --scenarios mixed  # some of them
  python -m scripts.eval_classifier --reuse <stamp>    # resume after a quota stop

Each scenario runs the UI and API suites with --reruns 2 and a set of injected faults
(app/faults.py), then classifies the failures with the real LLM. Ground truth:

- single-group scenarios (real_bug / environment_issue / flaky): every failing test belongs
  to that group's bucket, because only that group's faults are active;
- mixed (bugs + flaky + ENV_HEALTH_FAILING): a test that fails in the real_bug scenario fails
  deterministically because of a bug, so it is real_bug; any other failure is flaky. The
  health_only control run must show that ENV_HEALTH_FAILING alone fails nothing, otherwise
  those failures are reported as ambiguous and not scored;
- clean: nothing should fail; failures there are reported as instability, not scored.

Results go to samples/eval/: eval-report.md, eval-results.json and each scenario's
classification.json. Numbers are whatever the run produced; nothing is adjusted.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ai.classifier.classify import ClassificationReport, classify_run, load_records
from ai.classifier.payload import failing_tests
from ai.llm_client import LLMConfigError, LLMQuotaError, load_llm_config
from app.faults import FAULT_BUCKETS, Bucket

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
OUT = ROOT / "samples" / "eval"
BUCKETS = [b.value for b in Bucket]
PREDICTIONS = [*BUCKETS, "unclassified"]

BUGS = [f for f, b in FAULT_BUCKETS.items() if b is Bucket.REAL_BUG]
ENVS = [f for f, b in FAULT_BUCKETS.items() if b is Bucket.ENVIRONMENT_ISSUE]
FLAKY = [f for f, b in FAULT_BUCKETS.items() if b is Bucket.FLAKY]

SCENARIOS: dict[str, dict[str, Any]] = {
    "clean": {"faults": [], "classify": False},
    "real_bug": {"faults": BUGS, "classify": True, "truth": Bucket.REAL_BUG.value},
    "environment_issue": {"faults": ENVS, "classify": True,
                          "truth": Bucket.ENVIRONMENT_ISSUE.value},
    "flaky": {"faults": FLAKY, "classify": True, "truth": Bucket.FLAKY.value},
    "health_only": {"faults": ["ENV_HEALTH_FAILING"], "classify": False},
    "mixed": {"faults": [*BUGS, *FLAKY, "ENV_HEALTH_FAILING"], "classify": True},
}


def run_suite(name: str, faults: list[str], stamp: str) -> Path:
    run_id = f"eval-{stamp}-{name}"
    env = os.environ | {"FAULTS": ",".join(faults), "TESTMU_RUN_ID": run_id,
                        "TESTMU_CLASSIFY": "0"}
    print(f"[{name}] running tests with faults: {', '.join(faults) or 'none'}", flush=True)
    subprocess.run(
        [sys.executable, "-m", "pytest", "tests/ui", "tests/api", "-q", "-p", "no:cacheprovider",
         "--reruns", "2"],
        cwd=ROOT, env=env, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return REPORTS / f"run-{run_id}"


def failing_ids(run_dir: Path) -> set[str]:
    return set(failing_tests(load_records(run_dir)))


def ground_truth(name: str, failing: set[str], runs: dict[str, Path]) -> dict[str, str]:
    spec = SCENARIOS[name]
    if "truth" in spec:
        return {t: spec["truth"] for t in failing}
    if name == "mixed":
        bug_failures = failing_ids(runs["real_bug"]) if "real_bug" in runs else set()
        control_ok = "health_only" in runs and not failing_ids(runs["health_only"])
        truth = {}
        for test in failing:
            if test in bug_failures:
                truth[test] = Bucket.REAL_BUG.value
            elif control_ok:
                truth[test] = Bucket.FLAKY.value
            else:
                truth[test] = "ambiguous"
        return truth
    return {}


def score(results: list[dict[str, Any]]) -> dict[str, Any]:
    scored = [r for r in results if r["truth"] in BUCKETS]
    matrix = {t: dict.fromkeys(PREDICTIONS, 0) for t in BUCKETS}
    for r in scored:
        matrix[r["truth"]][r["predicted"]] += 1
    correct = sum(1 for r in scored if r["truth"] == r["predicted"])
    return {
        "scored": len(scored),
        "correct": correct,
        "accuracy": round(correct / len(scored), 3) if scored else None,
        "confusion_matrix": matrix,
    }


def render(summary: dict[str, Any]) -> str:
    s = summary["overall"]
    lines = [
        "# Flaky Test Classifier: evaluation",
        "",
        f"- Generated: {summary['generated_at_utc']}",
        f"- Model: `{summary['model']}`, prompt `classifier.{summary['prompt_version']}`,"
        " temperature 0",
        "- Each scenario: UI + API suites with `--reruns 2` and the faults listed; ground truth"
        " from `app/faults.py` as described in `scripts/eval_classifier.py`.",
        "",
        f"**Overall accuracy: {s['correct']}/{s['scored']}"
        f" = {s['accuracy'] if s['accuracy'] is not None else 'n/a'}**",
        "",
        "## Confusion matrix (rows: ground truth, columns: prediction)",
        "",
        "| | " + " | ".join(PREDICTIONS) + " |",
        "|---|" + "---|" * len(PREDICTIONS),
    ]
    for truth, row in s["confusion_matrix"].items():
        lines.append(f"| **{truth}** | " + " | ".join(str(row[p]) for p in PREDICTIONS) + " |")
    lines += ["", "## Per scenario", "",
              "| Scenario | Faults | Failing tests | Scored | Correct | Accuracy | LLM requests |",
              "|---|---|---|---|---|---|---|"]
    for name, sc in summary["scenarios"].items():
        acc = sc["score"]["accuracy"] if sc.get("score") else "—"
        lines.append(
            f"| {name} | {', '.join(sc['faults']) or 'none'} | {sc['failing']} |"
            f" {sc.get('score', {}).get('scored', '—')} | {sc.get('score', {}).get('correct', '—')}"
            f" | {acc} | {sc.get('llm_requests', 0)} |")
    misses = [r for sc in summary["scenarios"].values() for r in sc.get("results", [])
              if r["truth"] in BUCKETS and r["truth"] != r["predicted"]]
    lines += ["", f"## Misclassifications ({len(misses)})", ""]
    if misses:
        lines += ["| Scenario | Test | Truth | Predicted | Confidence | Model's reasoning |",
                  "|---|---|---|---|---|---|"]
        for r in misses:
            reasoning = r["reasoning"].replace("|", "\\|").replace("\n", " ")
            lines.append(f"| {r['scenario']} | `{r['test_id']}` | {r['truth']} |"
                         f" {r['predicted']} | {r['confidence']} | {reasoning} |")
    else:
        lines.append("None.")
    notes = [n for sc in summary["scenarios"].values() for n in sc.get("notes", [])]
    if notes:
        lines += ["", "## Notes", ""] + [f"- {n}" for n in notes]
    return "\n".join(lines) + "\n"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scenarios", nargs="+", choices=list(SCENARIOS),
                        default=list(SCENARIOS))
    parser.add_argument("--reuse", metavar="STAMP",
                        help="resume an evaluation: reuse its test runs and classifications")
    args = parser.parse_args()
    try:
        config = load_llm_config()
    except LLMConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    stamp = args.reuse or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out = OUT / stamp
    runs: dict[str, Path] = {}
    if args.reuse:  # earlier runs of this evaluation, also needed for mixed ground truth
        for name in SCENARIOS:
            run_dir = REPORTS / f"run-eval-{stamp}-{name}"
            if (run_dir / "execution-log.jsonl").exists():
                runs[name] = run_dir
    summary: dict[str, Any] = {"generated_at_utc": stamp, "model": config.model,
                               "prompt_version": None, "scenarios": {}}
    all_results: list[dict[str, Any]] = []

    for name in args.scenarios:
        spec = SCENARIOS[name]
        if name in runs:
            run_dir = runs[name]
            print(f"[{name}] reusing {run_dir.name}", flush=True)
        else:
            run_dir = run_suite(name, spec["faults"], stamp)
            runs[name] = run_dir
        failing = failing_ids(run_dir)
        entry: dict[str, Any] = {"faults": spec["faults"], "run_id": run_dir.name,
                                 "failing": len(failing), "notes": []}
        print(f"[{name}] {len(failing)} failing tests", flush=True)
        if name == "clean" and failing:
            entry["notes"].append(f"clean run had {len(failing)} failing tests (instability):"
                                  f" {sorted(failing)}")
        if name == "health_only" and failing:
            entry["notes"].append("ENV_HEALTH_FAILING alone failed tests; mixed-scenario"
                                  " failures outside the bug set are therefore not scored.")
        if spec["classify"] and failing:
            existing = run_dir / "classification.json"
            if args.reuse and existing.exists():
                report = ClassificationReport.model_validate_json(
                    existing.read_text(encoding="utf-8"))
                print(f"[{name}] reusing its classification", flush=True)
            else:
                try:
                    report = classify_run(run_dir, raise_on_quota=True)
                except LLMQuotaError as exc:
                    print(f"[{name}] stopped: {exc}", file=sys.stderr)
                    print(f"Resume later with: python -m scripts.eval_classifier --reuse {stamp}",
                          file=sys.stderr)
                    return 3
            summary["prompt_version"] = report.prompt_version
            truth = ground_truth(name, failing, runs)
            results = [{
                "scenario": name, "test_id": c.test_id, "case_id": c.case_id,
                "truth": truth.get(c.test_id, "ambiguous"), "predicted": c.bucket,
                "confidence": c.confidence, "reasoning": c.reasoning,
                "final_outcome": c.final_outcome,
            } for c in report.classifications]
            entry.update(results=results, score=score(results),
                         llm_requests=sum(c.attempts for c in report.llm_calls),
                         llm_calls=[c.model_dump() for c in report.llm_calls])
            all_results += results
            (out / name).mkdir(parents=True, exist_ok=True)
            shutil.copy(run_dir / "classification.json", out / name / "classification.json")
            shutil.copy(run_dir / "classification.md", out / name / "classification.md")
            print(f"[{name}] accuracy {entry['score']['accuracy']}", flush=True)
        summary["scenarios"][name] = entry

    summary["overall"] = score(all_results)
    out.mkdir(parents=True, exist_ok=True)
    (out / "eval-results.json").write_text(json.dumps(summary, indent=2) + "\n",
                                           encoding="utf-8", newline="\n")
    (out / "eval-report.md").write_text(render(summary), encoding="utf-8", newline="\n")
    print(f"Wrote {out.relative_to(ROOT)}/eval-report.md")
    print(f"Overall: {summary['overall']['correct']}/{summary['overall']['scored']}"
          f" = {summary['overall']['accuracy']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
