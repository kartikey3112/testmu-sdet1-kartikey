"""Login, logout, session handling, brute-force lockout and forgot-password flow.

Rules:
- Wrong password and unknown email get the same message (no user enumeration).
- LOCKOUT_THRESHOLD consecutive failures lock the account for LOCKOUT_MINUTES.
  A successful login resets the counter.
- Forgot-password responds the same whether or not the email exists. Reset tokens are
  single-use and expire after RESET_TOKEN_MINUTES; they are delivered to the test outbox.
- Sessions are cookie-based and expire SESSION_TTL_SECONDS after login.
"""

import hashlib
import hmac
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app import faults
from app.db import get_db
from app.settings import clock, settings
from app.web import templates

SESSION_COOKIE = "session"
MIN_PASSWORD_LENGTH = 8

MSG_INVALID = "Invalid email or password."
MSG_LOCKED = "Your account is locked after too many failed sign-in attempts. Try again later."
MSG_RESET_INVALID = "This reset link is invalid or has expired."
LOGIN_NOTICES = {
    "expired": "Your session has expired. Please sign in again.",
    "reset": "Your password has been updated. Please sign in.",
    "logged_out": "You have been signed out.",
}

router = APIRouter()
Db = Annotated[sqlite3.Connection, Depends(get_db)]


# --- Passwords -----------------------------------------------------------------------------

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt, digest = stored.split("$", 1)
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000)
    return hmac.compare_digest(candidate.hex(), digest)


# --- Authentication with lockout --------------------------------------------------------------

@dataclass(frozen=True)
class User:
    id: int
    email: str
    name: str
    role: str


class LoginResult(StrEnum):
    OK = "ok"
    INVALID = "invalid"
    LOCKED = "locked"


def _user(row: sqlite3.Row) -> User:
    return User(id=row["id"], email=row["email"], name=row["name"], role=row["role"])


def _is_locked(row: sqlite3.Row, now: datetime) -> bool:
    return row["locked_until"] is not None and datetime.fromisoformat(row["locked_until"]) > now


def _should_lock(failed_attempts: int) -> bool:
    if faults.is_active("BUG_LOCKOUT_THRESHOLD_WRONG"):
        return failed_attempts > settings.lockout_threshold
    return failed_attempts >= settings.lockout_threshold


def authenticate(
    conn: sqlite3.Connection, email: str, password: str
) -> tuple[LoginResult, User | None]:
    """Check credentials and apply the lockout rules. Shared by the login form and the API.

    Commits counter changes itself, because callers usually raise an error afterwards.
    """
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    if row is None:
        return LoginResult.INVALID, None

    now = clock.now()
    if _is_locked(row, now):
        return LoginResult.LOCKED, None

    if verify_password(password, row["password_hash"]):
        conn.execute(
            "UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?", (row["id"],)
        )
        conn.commit()
        return LoginResult.OK, _user(row)

    # A lock that has run out starts a fresh count.
    previous = 0 if row["locked_until"] else row["failed_attempts"]
    failed = previous + 1
    locked_until = None
    if _should_lock(failed):
        locked_until = (now + timedelta(minutes=settings.lockout_minutes)).isoformat()
    conn.execute(
        "UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?",
        (failed, locked_until, row["id"]),
    )
    conn.commit()
    return (LoginResult.LOCKED if locked_until else LoginResult.INVALID), None


# --- Sessions --------------------------------------------------------------------------------

class SessionState(StrEnum):
    VALID = "valid"
    MISSING = "missing"
    EXPIRED = "expired"


def create_session(conn: sqlite3.Connection, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = clock.now() + timedelta(seconds=settings.session_ttl_seconds)
    conn.execute(
        "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
        (token, user_id, expires_at.isoformat()),
    )
    return token


def session_user(conn: sqlite3.Connection, token: str | None) -> tuple[SessionState, User | None]:
    if not token:
        return SessionState.MISSING, None
    row = conn.execute(
        "SELECT s.expires_at, u.* FROM sessions s JOIN users u ON u.id = s.user_id"
        " WHERE s.token = ?",
        (token,),
    ).fetchone()
    if row is None:
        return SessionState.MISSING, None
    if datetime.fromisoformat(row["expires_at"]) <= clock.now():
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        return SessionState.EXPIRED, None
    return SessionState.VALID, _user(row)


class LoginRequired(Exception):  # noqa: N818 - control flow, not an error
    def __init__(self, reason: str | None) -> None:
        self.reason = reason


def require_page_user(request: Request, conn: Db) -> User:
    """Dependency for HTML pages: redirects to /login when there is no valid session."""
    state, user = session_user(conn, request.cookies.get(SESSION_COOKIE))
    if user is None:
        raise LoginRequired("expired" if state is SessionState.EXPIRED else None)
    return user


def login_redirect(reason: str | None) -> RedirectResponse:
    url = f"/login?reason={reason}" if reason else "/login"
    response = RedirectResponse(url, status_code=303)
    response.delete_cookie(SESSION_COOKIE)
    return response


# --- Login / logout pages --------------------------------------------------------------------

def _login_page(request: Request, *, error: str | None = None, email: str = "",
                status_code: int = 200) -> HTMLResponse:
    notice = LOGIN_NOTICES.get(request.query_params.get("reason", ""))
    return templates.TemplateResponse(
        request, "login.html", {"error": error, "notice": notice, "email": email},
        status_code=status_code,
    )


@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request) -> HTMLResponse:
    return _login_page(request)


@router.post("/login", response_model=None)
def login_submit(
    request: Request, conn: Db, email: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
) -> Response:
    result, user = authenticate(conn, email, password)
    if result is LoginResult.LOCKED:
        return _login_page(request, error=MSG_LOCKED, email=email, status_code=423)
    if user is None:
        return _login_page(request, error=MSG_INVALID, email=email, status_code=401)
    token = create_session(conn, user.id)
    response = RedirectResponse("/dashboard", status_code=303)
    response.set_cookie(
        SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=settings.session_ttl_seconds
    )
    return response


@router.post("/logout")
def logout(request: Request, conn: Db) -> RedirectResponse:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    return login_redirect("logged_out")


# --- Forgot / reset password -----------------------------------------------------------------

@router.get("/forgot-password", response_class=HTMLResponse)
def forgot_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "forgot_password.html", {"sent": False})


@router.post("/forgot-password", response_class=HTMLResponse)
def forgot_submit(request: Request, conn: Db, email: Annotated[str, Form()] = "") -> HTMLResponse:
    row = conn.execute(
        "SELECT id, email FROM users WHERE email = ?", (email.strip().lower(),)
    ).fetchone()
    if row is not None:
        token = secrets.token_urlsafe(32)
        now = clock.now()
        expires_at = now + timedelta(minutes=settings.reset_token_minutes)
        conn.execute(
            "INSERT INTO reset_tokens (token, user_id, expires_at) VALUES (?, ?, ?)",
            (token, row["id"], expires_at.isoformat()),
        )
        link = f"{str(request.base_url).rstrip('/')}/reset-password?token={token}"
        conn.execute(
            "INSERT INTO outbox (recipient, subject, body, token, created_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (row["email"], "Reset your TestMu Lite password",
             f"Use this link within {settings.reset_token_minutes} minutes: {link}",
             token, now.isoformat()),
        )
    # Same response either way, so the form can't be used to discover accounts.
    return templates.TemplateResponse(request, "forgot_password.html", {"sent": True})


def _valid_reset_token(conn: sqlite3.Connection, token: str) -> sqlite3.Row | None:
    row = conn.execute("SELECT * FROM reset_tokens WHERE token = ?", (token,)).fetchone()
    if row is None or row["used_at"] is not None:
        return None
    if datetime.fromisoformat(row["expires_at"]) <= clock.now():
        return None
    return row


def _reset_page(request: Request, token: str, *, error: str | None = None,
                valid: bool = True, status_code: int = 200) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "reset_password.html", {"token": token, "error": error, "valid": valid},
        status_code=status_code,
    )


@router.get("/reset-password", response_class=HTMLResponse)
def reset_form(request: Request, conn: Db, token: str = "") -> HTMLResponse:
    if _valid_reset_token(conn, token) is None:
        return _reset_page(request, token, error=MSG_RESET_INVALID, valid=False, status_code=400)
    return _reset_page(request, token)


@router.post("/reset-password", response_model=None)
def reset_submit(
    request: Request, conn: Db,
    token: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
    confirm_password: Annotated[str, Form()] = "",
) -> Response:
    row = _valid_reset_token(conn, token)
    if row is None:
        return _reset_page(request, token, error=MSG_RESET_INVALID, valid=False, status_code=400)
    if len(password) < MIN_PASSWORD_LENGTH:
        return _reset_page(
            request, token, error=f"Password must be at least {MIN_PASSWORD_LENGTH} characters.",
            status_code=422,
        )
    if password != confirm_password:
        return _reset_page(request, token, error="Passwords do not match.", status_code=422)

    conn.execute(
        "UPDATE users SET password_hash = ?, failed_attempts = 0, locked_until = NULL"
        " WHERE id = ?",
        (hash_password(password), row["user_id"]),
    )
    conn.execute(
        "UPDATE reset_tokens SET used_at = ? WHERE token = ?", (clock.now().isoformat(), token)
    )
    conn.execute("DELETE FROM sessions WHERE user_id = ?", (row["user_id"],))
    return RedirectResponse("/login?reason=reset", status_code=303)
