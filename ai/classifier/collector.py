"""pytest plugin that records one JSON line per test attempt to execution-log.jsonl.

It implements the framework's pytest_testmu_attempt_finished hook, so it sees every attempt,
including pytest-rerunfailures reruns (run with --reruns 2 to give the classifier rerun
evidence). Files written to reports/run-<id>/:

  execution-log.jsonl  one line per attempt (input to the classifier)
  run-meta.json        git SHA, versions, base URL, active faults. Active faults are for the
                       evaluation only and are never read by the payload builder.

At session end, if LLM_API_KEY is set and something failed, the run is classified and the
result is added to the HTML report. Turn that off with TESTMU_CLASSIFY=0.
"""

import json
import os
import platform
import subprocess
from importlib.metadata import version
from pathlib import Path
from typing import Any

import httpx
import pytest

from ai.classifier import report as html_report
from framework.evidence import Evidence
from framework.pytest_plugin import run_dir

LOG_NAME = "execution-log.jsonl"
META_NAME = "run-meta.json"
TRACEBACK_CHARS = 2000
LOG_LINES = 20
MODULE_FOLDERS = ("login", "dashboard", "api", "unit")

_BASE_URL_KEY = pytest.StashKey[str | None]()
_BROWSER_KEY = pytest.StashKey[str | None]()


def _module(item: pytest.Item) -> str:
    parts = item.path.parts
    return next((p for p in reversed(parts) if p in MODULE_FOLDERS), "other")


def _case_id(item: pytest.Item) -> str | None:
    marker = item.get_closest_marker("case")
    return marker.args[0] if marker else None


def _location(report: pytest.TestReport, crash: Any) -> str | None:
    if crash is None:
        return None
    path = Path(crash.path)
    try:
        path = path.relative_to(Path.cwd())
    except ValueError:
        pass
    return f"{path.as_posix()}:{crash.lineno}"


def _error(report: pytest.TestReport) -> dict[str, Any] | None:
    if report.passed or report.skipped:
        return None
    crash = getattr(report.longrepr, "reprcrash", None)
    message = crash.message if crash else str(report.longrepr).splitlines()[-1]
    error_type, sep, rest = message.partition(": ")
    if not sep or " " in error_type:
        error_type, rest = "Error", message
    log_lines = [line for line in (report.caplog or "").splitlines() if line.strip()]
    return {
        "phase": report.when,
        "type": error_type.rsplit(".", 1)[-1],
        "message": rest,
        "location": _location(report, crash),
        "traceback_tail": report.longreprtext[-TRACEBACK_CHARS:],
        "log_lines": log_lines[-LOG_LINES:],
    }


def _health(base_url: str | None) -> dict[str, Any] | None:
    if not base_url:
        return None
    try:
        response = httpx.get(f"{base_url}/health", timeout=3)
        return {"status": response.status_code, "body": response.text[:300]}
    except httpx.HTTPError as exc:
        return {"status": None, "error": f"{type(exc).__name__}: {exc}"[:300]}


def _remember_context(item: pytest.Item) -> None:
    funcargs = getattr(item, "funcargs", {})
    if funcargs.get("base_url"):
        item.config.stash[_BASE_URL_KEY] = funcargs["base_url"]
    browser = funcargs.get("browser")
    if browser is not None and not item.config.stash.get(_BROWSER_KEY, None):
        item.config.stash[_BROWSER_KEY] = f"{browser.browser_type.name} {browser.version}"


def classification_wanted() -> bool:
    return os.getenv("TESTMU_CLASSIFY", "1") != "0" and bool(os.getenv("LLM_API_KEY"))


_config: pytest.Config | None = None  # for the pytest-html hooks, which don't receive config


def pytest_configure(config: pytest.Config) -> None:
    global _config
    _config = config
    config.stash[_BASE_URL_KEY] = None
    config.stash[_BROWSER_KEY] = None
    (run_dir(config) / LOG_NAME).write_text("", encoding="utf-8")
    html_report.enable_column(config, classification_wanted())


def pytest_html_results_table_header(cells: list[str]) -> None:
    if _config is not None:
        html_report.add_header(_config, cells)


def pytest_html_results_table_row(report: pytest.TestReport, cells: list[str]) -> None:
    if _config is not None:
        html_report.add_row(_config, cells)


def pytest_testmu_attempt_finished(
    item: pytest.Item, report: pytest.TestReport, evidence: Evidence, attempt: int
) -> None:
    _remember_context(item)
    failed = report.failed
    record: dict[str, Any] = {
        "nodeid": item.nodeid,
        "case_id": _case_id(item),
        "module": _module(item),
        "layer": "ui" if "ui" in item.path.parts else ("api" if "api" in item.path.parts
                                                        else "unit"),
        "attempt": attempt,
        "outcome": "passed" if report.passed else ("error" if report.when == "setup"
                                                   else "failed"),
        "duration_s": round(report.duration, 3),
    }
    if failed:
        record["error"] = _error(report)
        record["api"] = evidence.last_api_exchange
        record["ui"] = {
            "page_url": evidence.page_url,
            "console_errors": evidence.console_errors,
            "failed_requests": evidence.failed_requests,
            "screenshot_paths": evidence.screenshot_paths,  # paths only; images are not sent
        } if evidence.pages else None
        record["health_at_failure"] = _health(item.config.stash[_BASE_URL_KEY])
    with (run_dir(item.config) / LOG_NAME).open("a", encoding="utf-8", newline="\n") as log:
        log.write(json.dumps(record, ensure_ascii=False) + "\n")


def _git_sha() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def _has_failures(log_path: Path) -> bool:
    with log_path.open(encoding="utf-8") as log:
        return any(json.loads(line)["outcome"] != "passed" for line in log if line.strip())


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Write run metadata, then classify failures if an LLM key is configured.

    Runs before pytest-html's own sessionfinish (which is trylast and writes the report),
    so the classification can still be added to the report.
    """
    config = session.config
    # Session fixtures, including the app server, are already torn down here, so active
    # faults come from the FAULTS env var, which is how evaluation runs set them.
    meta = {
        "run_id": run_dir(config).name.removeprefix("run-"),
        "git_sha": _git_sha(),
        "python": platform.python_version(),
        "playwright": version("playwright"),
        "browser": config.stash.get(_BROWSER_KEY, None),
        "base_url": config.stash.get(_BASE_URL_KEY, None),
        "reruns": getattr(config.option, "reruns", 0),
        "active_faults_for_evaluation_only": sorted(
            f for f in os.getenv("FAULTS", "").split(",") if f.strip()
        ),
    }
    (run_dir(config) / META_NAME).write_text(json.dumps(meta, indent=2) + "\n",
                                             encoding="utf-8", newline="\n")

    if not classification_wanted() or not _has_failures(run_dir(config) / LOG_NAME):
        return
    from ai.classifier.classify import classify_run  # imported late: only needed with a key

    result = classify_run(run_dir(config))
    html_report.attach_to_html_report(config, result)
