"""Test-only endpoints under /_test. Mounted only when TEST_MODE=1; otherwise they don't exist."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app import faults
from app.api import rate_limiter
from app.db import get_db
from app.errors import ApiError
from app.seed import reset_database
from app.settings import clock, settings

router = APIRouter(prefix="/_test", tags=["test-only"])
Db = Annotated[sqlite3.Connection, Depends(get_db)]


class FaultsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    faults: list[str]


class ClockRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    advance_seconds: float = Field(gt=0)


def _read_sessions() -> list[tuple]:
    # Direct connection on purpose: reset must work even while ENV_DB_UNAVAILABLE is active.
    conn = sqlite3.connect(settings.db_path)
    try:
        return conn.execute("SELECT token, user_id, expires_at FROM sessions").fetchall()
    finally:
        conn.close()


def _restore_sessions(sessions: list[tuple]) -> None:
    conn = sqlite3.connect(settings.db_path)
    try:
        conn.executemany(
            "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)", sessions
        )
        conn.commit()
    finally:
        conn.close()


def _faults_state() -> dict:
    return {
        "active": faults.active(),
        "available": {name: bucket.value for name, bucket in faults.FAULT_BUCKETS.items()},
    }


@router.get("/outbox")
def outbox(conn: Db, to: str | None = None) -> dict:
    query = "SELECT * FROM outbox"
    params: tuple = ()
    if to:
        query += " WHERE recipient = ?"
        params = (to.strip().lower(),)
    rows = conn.execute(query + " ORDER BY id", params).fetchall()
    return {"messages": [dict(r) for r in rows]}


@router.get("/faults")
def get_faults() -> dict:
    return _faults_state()


@router.post("/faults")
def set_faults(body: FaultsRequest) -> dict:
    try:
        faults.set_active(body.faults)
    except faults.UnknownFaultError as exc:
        raise ApiError(422, "unknown_fault", str(exc)) from exc
    return _faults_state()


@router.get("/clock")
def get_clock() -> dict:
    return {"now": clock.now().isoformat(), "offset_seconds": clock.offset.total_seconds()}


@router.post("/clock")
def advance_clock(body: ClockRequest) -> dict:
    clock.advance(body.advance_seconds)
    return get_clock()


@router.post("/reset")
def reset(keep_sessions: bool = False) -> dict:
    """Reload seed data and restore faults, clock and rate limits to their startup state.

    keep_sessions=true carries existing login sessions over, so the test framework can reuse
    cached browser logins between tests. Seed user IDs are stable, so the sessions stay valid.
    """
    sessions = _read_sessions() if keep_sessions else []
    reset_database()
    if sessions:
        _restore_sessions(sessions)
    faults.reset()
    clock.reset()
    rate_limiter.reset()
    return {"status": "reset", **_faults_state()}
