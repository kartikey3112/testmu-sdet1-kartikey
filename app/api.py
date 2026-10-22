"""REST API under /api/v1: token auth, test-case CRUD, rate limiting, error format.

Auth: POST /auth/token returns a JWT. Missing, malformed or expired tokens get 401;
a role that isn't allowed gets 403. Dashboard widget endpoints (app/dashboard.py) also
accept the browser session cookie so the UI can call them.
"""

import math
import sqlite3
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app import faults
from app.auth import SESSION_COOKIE, LoginResult, User, authenticate, session_user
from app.db import get_db
from app.errors import ApiError
from app.settings import clock, settings

router = APIRouter(prefix="/api/v1")
Db = Annotated[sqlite3.Connection, Depends(get_db)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Tokens ----------------------------------------------------------------------------------

class TokenRequest(StrictModel):
    email: str
    password: str


class TokenResponse(StrictModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    expires_at: datetime


def issue_token(user: User) -> TokenResponse:
    now = clock.now()
    expires_at = now + timedelta(seconds=settings.token_ttl_seconds)
    claims = {
        "sub": str(user.id), "email": user.email, "role": user.role,
        "iat": int(now.timestamp()), "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(claims, settings.jwt_secret, algorithm="HS256")
    return TokenResponse(
        access_token=token, expires_in=settings.token_ttl_seconds,
        expires_at=expires_at.replace(microsecond=0),
    )


def decode_token(token: str) -> dict:
    try:
        # Expiry is checked against the app clock below, so the test clock applies to it.
        claims = jwt.decode(
            token, settings.jwt_secret, algorithms=["HS256"],
            options={"verify_exp": False, "require": ["exp", "sub", "role"]},
        )
    except jwt.PyJWTError as exc:
        raise ApiError(
            401, "invalid_token", "Token is malformed or has an invalid signature"
        ) from exc
    if datetime.fromtimestamp(claims["exp"], UTC) <= clock.now():
        raise ApiError(401, "token_expired", "Token has expired")
    return claims


@router.post("/auth/token", response_model=TokenResponse, tags=["auth"])
def create_token(body: TokenRequest, conn: Db) -> TokenResponse:
    result, user = authenticate(conn, body.email, body.password)
    if result is LoginResult.LOCKED:
        raise ApiError(423, "account_locked", "Account is locked after too many failed attempts")
    if user is None:
        raise ApiError(401, "invalid_credentials", "Invalid email or password")
    return issue_token(user)


# --- Rate limiting ---------------------------------------------------------------------------

class RateLimiter:
    """Fixed one-minute window per token, using the app clock."""

    def __init__(self) -> None:
        self.windows: dict[str, tuple[int, int]] = {}

    def check(self, key: str) -> None:
        now = clock.now().timestamp()
        window = int(now // 60)
        start, count = self.windows.get(key, (window, 0))
        if start != window:
            start, count = window, 0
        if count >= settings.rate_limit_per_min:
            retry_after = max(1, math.ceil((window + 1) * 60 - now))
            raise ApiError(
                429, "rate_limited",
                f"Rate limit of {settings.rate_limit_per_min} requests per minute exceeded",
                headers={"Retry-After": str(retry_after)},
            )
        self.windows[key] = (start, count + 1)

    def reset(self) -> None:
        self.windows.clear()


rate_limiter = RateLimiter()


# --- Current principal -----------------------------------------------------------------------

def current_user(request: Request, conn: Db) -> User:
    """Bearer token first; fall back to the session cookie for calls made by the dashboard UI."""
    header = request.headers.get("Authorization")
    if header is not None:
        scheme, _, token = header.partition(" ")
        if scheme.lower() != "bearer" or not token.strip():
            raise ApiError(401, "invalid_token", "Authorization header must be 'Bearer <token>'")
        claims = decode_token(token.strip())
        rate_limiter.check(token.strip())
        row = conn.execute("SELECT * FROM users WHERE id = ?", (int(claims["sub"]),)).fetchone()
        if row is None:
            raise ApiError(401, "invalid_token", "Token user no longer exists")
        return User(id=row["id"], email=row["email"], name=row["name"], role=row["role"])

    _, user = session_user(conn, request.cookies.get(SESSION_COOKIE))
    if user is None:
        raise ApiError(401, "missing_token", "Authentication required")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def require_admin(user: CurrentUser) -> User:
    if user.role != "admin":
        raise ApiError(403, "forbidden", "Admin role required")
    return user


AdminUser = Annotated[User, Depends(require_admin)]


# --- Test cases ------------------------------------------------------------------------------

class Module(StrEnum):
    LOGIN = "login"
    DASHBOARD = "dashboard"
    API = "api"


class Priority(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


def _clean_title(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("must not be blank")
    return value


class CaseCreate(StrictModel):
    title: str = Field(max_length=200)
    module: Module
    priority: Priority
    description: str = Field(default="", max_length=2000)

    _title = field_validator("title")(_clean_title)


class CaseUpdate(StrictModel):
    title: str | None = Field(default=None, max_length=200)
    module: Module | None = None
    priority: Priority | None = None
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("title")
    @classmethod
    def _title(cls, value: str | None) -> str | None:
        return None if value is None else _clean_title(value)


class CaseOut(StrictModel):
    id: int
    title: str
    module: Module
    priority: Priority
    description: str
    created_at: datetime
    updated_at: datetime


class CasePage(StrictModel):
    items: list[CaseOut]
    page: int
    page_size: int
    total: int


def _get_case(conn: sqlite3.Connection, case_id: int) -> CaseOut:
    row = conn.execute("SELECT * FROM test_cases WHERE id = ?", (case_id,)).fetchone()
    if row is None:
        raise ApiError(404, "not_found", f"Test case {case_id} not found")
    return CaseOut(**dict(row))


def _check_unique_title(
    conn: sqlite3.Connection, title: str, exclude_id: int | None = None
) -> None:
    row = conn.execute(
        "SELECT id FROM test_cases WHERE title = ? AND id IS NOT ?", (title, exclude_id)
    ).fetchone()
    if row is not None:
        raise ApiError(409, "duplicate_title", f"A test case titled '{title}' already exists")


@router.get("/test-cases", response_model=CasePage, tags=["test-cases"])
def list_test_cases(
    conn: Db, _: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> CasePage:
    total = conn.execute("SELECT COUNT(*) FROM test_cases").fetchone()[0]
    rows = conn.execute(
        "SELECT * FROM test_cases ORDER BY id LIMIT ? OFFSET ?", (page_size, (page - 1) * page_size)
    ).fetchall()
    return CasePage(
        items=[CaseOut(**dict(r)) for r in rows], page=page, page_size=page_size, total=total
    )


@router.get("/test-cases/{case_id}", response_model=CaseOut, tags=["test-cases"])
def get_test_case(case_id: int, conn: Db, _: CurrentUser) -> CaseOut:
    return _get_case(conn, case_id)


@router.post("/test-cases", response_model=CaseOut, status_code=201, tags=["test-cases"])
def create_test_case(body: CaseCreate, conn: Db, _: AdminUser) -> CaseOut:
    _check_unique_title(conn, body.title)
    now = clock.now().isoformat()
    cursor = conn.execute(
        "INSERT INTO test_cases (title, module, priority, description, created_at, updated_at)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (body.title, body.module, body.priority, body.description, now, now),
    )
    return _get_case(conn, cursor.lastrowid)


@router.patch("/test-cases/{case_id}", response_model=CaseOut, tags=["test-cases"])
def update_test_case(case_id: int, body: CaseUpdate, conn: Db, _: AdminUser) -> CaseOut:
    _get_case(conn, case_id)
    changes = body.model_dump(exclude_none=True)
    if "title" in changes:
        _check_unique_title(conn, changes["title"], exclude_id=case_id)
    if changes:
        changes["updated_at"] = clock.now().isoformat()
        assignments = ", ".join(f"{column} = ?" for column in changes)
        conn.execute(
            f"UPDATE test_cases SET {assignments} WHERE id = ?", (*changes.values(), case_id)
        )
    return _get_case(conn, case_id)


@router.delete("/test-cases/{case_id}", status_code=204, tags=["test-cases"])
def delete_test_case(case_id: int, conn: Db, _: AdminUser) -> Response:
    _get_case(conn, case_id)
    if not faults.is_active("BUG_DELETE_NOT_PERSISTED"):
        conn.execute("DELETE FROM test_cases WHERE id = ?", (case_id,))
    return Response(status_code=204)
