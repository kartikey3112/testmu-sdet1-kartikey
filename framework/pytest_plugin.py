"""pytest plugin: run folder, report paths, failure artifacts and the Task 3 hook point.

Each pytest session writes to reports/run-<id>/:
  report.html   self-contained pytest-html report
  junit.xml     JUnit XML
  artifacts/    screenshots and Playwright traces of failed attempts
  case-results.json  outcome per test linked to a generated case
"""

import base64
import html
import json
import re
from datetime import datetime
from pathlib import Path

import pytest
from playwright.sync_api import expect
from pytest_html import extras

from framework import hookspecs
from framework.config import config as framework_config
from framework.evidence import evidence_for, reset_evidence

RUN_DIR_KEY = pytest.StashKey[Path]()
REPORTS_KEY = pytest.StashKey[dict[str, pytest.TestReport]]()


def pytest_addhooks(pluginmanager: pytest.PytestPluginManager) -> None:
    pluginmanager.add_hookspecs(hookspecs)


@pytest.hookimpl(tryfirst=True)  # before pytest-html and junitxml read their output paths
def pytest_configure(config: pytest.Config) -> None:
    run_id = framework_config.run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
    reports_dir = Path(framework_config.reports_dir)
    run_dir = reports_dir / f"run-{run_id}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "latest-run.txt").write_text(run_id, encoding="utf-8")
    config.stash[RUN_DIR_KEY] = run_dir

    if not config.option.htmlpath:
        config.option.htmlpath = str(run_dir / "report.html")
        config.option.self_contained_html = True
    if not config.option.xmlpath:
        config.option.xmlpath = str(run_dir / "junit.xml")

    expect.set_options(timeout=framework_config.expect_timeout_ms)


def run_dir(config: pytest.Config) -> Path:
    return config.stash[RUN_DIR_KEY]


def attempt_number(item: pytest.Item) -> int:
    # pytest-rerunfailures sets execution_count: 1 for the first run, 2 for the first rerun...
    return getattr(item, "execution_count", 1)


def artifact_dir(item: pytest.Item) -> Path:
    safe = re.sub(r"[^\w.-]+", "_", item.nodeid)[-120:]
    return run_dir(item.config) / "artifacts" / safe / f"attempt-{attempt_number(item)}"


def test_failed(item: pytest.Item) -> bool:
    reports = item.stash.get(REPORTS_KEY, {})
    return any(r.failed for r in reports.values())


CASE_RESULTS_KEY = pytest.StashKey[dict[str, dict]]()


def pytest_sessionstart(session: pytest.Session) -> None:
    session.config.stash[CASE_RESULTS_KEY] = {}


def _record_case_result(item: pytest.Item, report: pytest.TestReport) -> None:
    """Keep the latest outcome of every test linked to a generated case (@pytest.mark.case).

    Written to case-results.json at session end; scripts/build_traceability.py reads it.
    """
    case_ids = [m.args[0] for m in item.iter_markers("case")]
    if not case_ids:
        return
    if report.when == "call" or not report.passed:
        results = item.config.stash[CASE_RESULTS_KEY]
        results[item.nodeid] = {"cases": case_ids, "outcome": report.outcome,
                                "attempt": attempt_number(item)}


def pytest_sessionfinish(session: pytest.Session) -> None:
    results = session.config.stash.get(CASE_RESULTS_KEY, {})
    if results:
        path = run_dir(session.config) / "case-results.json"
        path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8", newline="\n")


def pytest_html_report_title(report) -> None:
    report.title = "TestMu Lite test report"


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item: pytest.Item) -> None:
    item.stash[REPORTS_KEY] = {}
    reset_evidence(item)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report: pytest.TestReport = outcome.get_result()
    item.stash.setdefault(REPORTS_KEY, {})[report.when] = report
    _record_case_result(item, report)

    if report.failed and report.when in ("setup", "call"):
        _capture_failure(item, report)

    attempt_over = report.when == "call" or (report.when == "setup" and not report.passed)
    if attempt_over and not report.skipped:
        item.config.hook.pytest_testmu_attempt_finished(
            item=item, report=report, evidence=evidence_for(item), attempt=attempt_number(item)
        )


def _capture_failure(item: pytest.Item, report: pytest.TestReport) -> None:
    evidence = evidence_for(item)
    report_extras = getattr(report, "extras", [])
    out = artifact_dir(item)
    out.mkdir(parents=True, exist_ok=True)
    report_dir = run_dir(item.config)

    for i, page in enumerate(evidence.pages):
        if page.is_closed():
            continue
        evidence.page_url = page.url
        png = page.screenshot(full_page=True)
        path = out / f"screenshot-{i}.png"
        path.write_bytes(png)
        evidence.screenshot_paths.append(str(path))
        report_extras.append(extras.png(base64.b64encode(png).decode(), name=f"Screenshot {i}"))

    for trace in evidence.trace_paths:
        rel = Path(trace).relative_to(report_dir).as_posix()
        report_extras.append(extras.url(rel, name="Playwright trace (playwright show-trace)"))

    sections = {
        "Page URL": evidence.page_url,
        "Console errors": "\n".join(evidence.console_errors),
        "Failed or 4xx/5xx network requests": "\n".join(evidence.failed_requests),
        "Last API exchange": evidence.last_api_exchange and "\n".join(
            f"{k}: {v}" for k, v in evidence.last_api_exchange.items()
        ),
    }
    body = "".join(
        f"<h4>{html.escape(title)}</h4><pre>{html.escape(str(value))}</pre>"
        for title, value in sections.items() if value
    )
    if body:
        report_extras.append(extras.html(f"<div class='testmu-evidence'>{body}</div>"))
    report.extras = report_extras
