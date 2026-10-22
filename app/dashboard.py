"""Dashboard page and the per-widget JSON endpoints it loads from.

Each widget loads from its own endpoint under /api/v1/dashboard, so a test can compare
UI value == API value == expected-from-seed. Admin-only widgets are left out of the page
for viewers and their endpoints return 403.
"""

import asyncio
import random
import sqlite3
from datetime import date
from enum import StrEnum
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict

from app import faults
from app.api import AdminUser, CurrentUser
from app.auth import User, require_page_user
from app.db import get_db
from app.errors import ApiError
from app.settings import settings
from app.web import templates

page_router = APIRouter()
Db = Annotated[sqlite3.Connection, Depends(get_db)]


@page_router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(
    request: Request, user: Annotated[User, Depends(require_page_user)]
) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "dashboard.html", {"user": user, "is_admin": user.role == "admin"}
    )


# --- Widget endpoints ------------------------------------------------------------------------

async def widget_faults() -> None:
    if faults.is_active("ENV_WIDGET_API_503"):
        raise ApiError(503, "upstream_unavailable", "Metrics service is unavailable")
    if (
        faults.is_active("FLAKY_WIDGET_LATENCY")
        and random.random() < settings.flaky_latency_probability
    ):
        await asyncio.sleep(settings.flaky_latency_seconds)


widget_router = APIRouter(
    prefix="/api/v1/dashboard", tags=["dashboard"], dependencies=[Depends(widget_faults)]
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CountWidget(StrictModel):
    value: int


class PassRateWidget(StrictModel):
    value: float
    run_id: int
    run_name: str


class RunStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"


class RunSort(StrEnum):
    DATE = "date"
    PASS_RATE = "pass_rate"


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


class Run(StrictModel):
    id: int
    name: str
    run_date: date
    total: int
    passed: int
    failed: int
    pass_rate: float
    status: RunStatus


class RunList(StrictModel):
    items: list[Run]


class FlakyTest(StrictModel):
    test_name: str
    flips: int
    last_seen: date


class FlakyTestList(StrictModel):
    items: list[FlakyTest]


class Activity(StrictModel):
    user_email: str
    action: str
    at: str


class ActivityList(StrictModel):
    items: list[Activity]


def pass_rate(passed: int, total: int) -> float:
    return round(passed * 100 / total, 1) if total else 0.0


def _run(row: sqlite3.Row) -> Run:
    return Run(
        id=row["id"], name=row["name"], run_date=row["run_date"], total=row["total"],
        passed=row["passed"], failed=row["failed"],
        pass_rate=pass_rate(row["passed"], row["total"]),
        status=RunStatus.PASSED if row["failed"] == 0 else RunStatus.FAILED,
    )


@widget_router.get("/total-test-cases", response_model=CountWidget)
def total_test_cases(conn: Db, _: CurrentUser) -> CountWidget:
    return CountWidget(value=conn.execute("SELECT COUNT(*) FROM test_cases").fetchone()[0])


@widget_router.get("/pass-rate", response_model=PassRateWidget)
def latest_pass_rate(conn: Db, _: CurrentUser) -> PassRateWidget:
    runs = conn.execute("SELECT * FROM runs ORDER BY run_date DESC, id DESC LIMIT 2").fetchall()
    if not runs:
        raise ApiError(404, "not_found", "No runs yet")
    index = 1 if faults.is_active("BUG_PASS_RATE_OFF_BY_ONE") and len(runs) > 1 else 0
    run = runs[index]
    return PassRateWidget(
        value=pass_rate(run["passed"], run["total"]), run_id=run["id"], run_name=run["name"]
    )


@widget_router.get("/recent-runs", response_model=RunList)
def recent_runs(
    conn: Db, _: CurrentUser,
    status: RunStatus | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    sort: RunSort | None = None,
    order: SortOrder = SortOrder.DESC,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> RunList:
    if date_from and date_to and date_from > date_to:
        raise ApiError(422, "validation_error", "date_from must be on or before date_to")

    runs = [_run(r) for r in conn.execute("SELECT * FROM runs").fetchall()]
    if status:
        runs = [r for r in runs if r.status == status]
    if date_from:
        runs = [r for r in runs if r.run_date >= date_from]
    if date_to:
        runs = [r for r in runs if r.run_date <= date_to]

    # Newest first is the default and the tie-break for pass-rate sorting.
    runs.sort(key=lambda r: (r.run_date, r.id), reverse=True)
    if sort is RunSort.PASS_RATE:
        runs.sort(key=lambda r: r.pass_rate, reverse=order is SortOrder.DESC)
    elif sort is RunSort.DATE and order is SortOrder.ASC:
        runs.reverse()
    elif sort is None and faults.is_active("FLAKY_UNSORTED_ORDER"):
        random.shuffle(runs)
    return RunList(items=runs[:limit])


@widget_router.get("/flaky-tests", response_model=FlakyTestList)
def flaky_tests(conn: Db, _: AdminUser) -> FlakyTestList:
    rows = conn.execute("SELECT * FROM flaky_tests ORDER BY flips DESC, id").fetchall()
    return FlakyTestList(
        items=[FlakyTest(test_name=r["test_name"], flips=r["flips"], last_seen=r["last_seen"])
               for r in rows]
    )


@widget_router.get("/team-activity", response_model=ActivityList)
def team_activity(conn: Db, _: AdminUser) -> ActivityList:
    rows = conn.execute("SELECT * FROM activity ORDER BY at DESC").fetchall()
    return ActivityList(
        items=[Activity(user_email=r["user_email"], action=r["action"], at=r["at"]) for r in rows]
    )
