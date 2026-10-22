"""SQLite connection and schema."""

import sqlite3
from collections.abc import Iterator

from app import faults
from app.settings import settings

SCHEMA = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'viewer')),
    password_hash TEXT NOT NULL,
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until TEXT
);
CREATE TABLE sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    expires_at TEXT NOT NULL
);
CREATE TABLE reset_tokens (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    expires_at TEXT NOT NULL,
    used_at TEXT
);
CREATE TABLE outbox (
    id INTEGER PRIMARY KEY,
    recipient TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    token TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE test_cases (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL UNIQUE COLLATE NOCASE,
    module TEXT NOT NULL,
    priority TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE runs (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    run_date TEXT NOT NULL,
    total INTEGER NOT NULL,
    passed INTEGER NOT NULL,
    failed INTEGER NOT NULL
);
CREATE TABLE flaky_tests (
    id INTEGER PRIMARY KEY,
    test_name TEXT NOT NULL,
    flips INTEGER NOT NULL,
    last_seen TEXT NOT NULL
);
CREATE TABLE activity (
    id INTEGER PRIMARY KEY,
    user_email TEXT NOT NULL,
    action TEXT NOT NULL,
    at TEXT NOT NULL
);
"""

TABLES = ["activity", "flaky_tests", "runs", "test_cases", "outbox", "reset_tokens", "sessions",
          "users"]


def connect() -> sqlite3.Connection:
    if faults.is_active("ENV_DB_UNAVAILABLE"):
        raise sqlite3.OperationalError("unable to open database file")
    conn = sqlite3.connect(settings.db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency: one connection per request, committed on success."""
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def recreate_schema(conn: sqlite3.Connection) -> None:
    for table in TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.executescript(SCHEMA)
