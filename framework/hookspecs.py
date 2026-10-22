"""Custom pytest hook declared by the framework."""

import pytest

from framework.evidence import Evidence


@pytest.hookspec
def pytest_testmu_attempt_finished(
    item: pytest.Item, report: pytest.TestReport, evidence: Evidence, attempt: int
) -> None:
    """Called once per test attempt, after its outcome is known.

    `report` is the call-phase report, or the setup report if setup failed. `attempt` starts
    at 1 and increases with each pytest-rerunfailures rerun.
    """
