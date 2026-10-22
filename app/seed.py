"""Deterministic seed data and the database reset entry point.

Run `python -m app.seed` to reset the database to this data. Tests compute expected
dashboard values from these constants, so UI value == API value == expected-from-seed.
Passwords here are test-only credentials for a local app.
"""

import sqlite3

from app import db
from app.auth import hash_password
from app.settings import settings

SEED_TIME = "2026-09-01T09:00:00+00:00"

SEED_USERS = [
    {"email": "admin@testmu.local", "name": "Asha Admin", "role": "admin",
     "password": "Admin@12345"},
    {"email": "viewer@testmu.local", "name": "Vik Viewer", "role": "viewer",
     "password": "Viewer@12345"},
]

SEED_TEST_CASES = [
    ("Login with valid credentials", "login", "P0"),
    ("Login with wrong password shows generic error", "login", "P0"),
    ("Login with unknown email shows generic error", "login", "P0"),
    ("Account locks after repeated failures", "login", "P0"),
    ("Forgot password sends reset link", "login", "P1"),
    ("Reset link cannot be reused", "login", "P1"),
    ("Expired session redirects to login", "login", "P1"),
    ("Logout clears session", "login", "P2"),
    ("Total test cases widget shows count", "dashboard", "P0"),
    ("Pass rate widget shows latest run", "dashboard", "P0"),
    ("Recent runs filter by status", "dashboard", "P1"),
    ("Recent runs sort by pass rate", "dashboard", "P1"),
    ("Flaky tests widget hidden for viewer", "dashboard", "P0"),
    ("Team activity widget hidden for viewer", "dashboard", "P1"),
    ("Sidebar collapses on mobile", "dashboard", "P2"),
    ("Widget shows error state when API fails", "dashboard", "P2"),
    ("Token issued for valid credentials", "api", "P0"),
    ("Expired token rejected", "api", "P0"),
    ("Create test case", "api", "P0"),
    ("Duplicate title rejected", "api", "P1"),
    ("Unknown ID returns 404", "api", "P1"),
    ("Viewer cannot delete test case", "api", "P0"),
    ("Rate limit returns 429", "api", "P1"),
    ("List is paginated", "api", "P2"),
]

# (run_date, total, passed). The latest run is last; its pass rate differs from the previous
# run so an off-by-one read is visible.
SEED_RUNS = [
    ("2026-09-10", 24, 24),
    ("2026-09-11", 24, 22),
    ("2026-09-12", 24, 23),
    ("2026-09-13", 24, 24),
    ("2026-09-14", 24, 20),
    ("2026-09-15", 24, 24),
    ("2026-09-16", 24, 23),
    ("2026-09-17", 24, 21),
    ("2026-09-18", 24, 24),
    ("2026-09-19", 24, 22),
    ("2026-09-20", 24, 24),
    ("2026-09-21", 24, 21),
]

SEED_FLAKY_TESTS = [
    ("tests/ui/dashboard/test_widgets.py::test_recent_runs_loads", 4, "2026-09-21"),
    ("tests/ui/login/test_login.py::test_session_expiry", 3, "2026-09-20"),
    ("tests/api/test_rate_limit.py::test_429_after_limit", 2, "2026-09-19"),
    ("tests/ui/dashboard/test_layout.py::test_mobile_menu", 1, "2026-09-17"),
]

SEED_ACTIVITY = [
    ("admin@testmu.local", "Created test case 'Rate limit returns 429'",
     "2026-09-21T10:15:00+00:00"),
    ("viewer@testmu.local", "Viewed run 2026-09-21 nightly", "2026-09-21T09:40:00+00:00"),
    ("admin@testmu.local", "Marked 'test_session_expiry' as flaky", "2026-09-20T16:05:00+00:00"),
    ("admin@testmu.local", "Started run 2026-09-20 nightly", "2026-09-20T02:00:00+00:00"),
    ("viewer@testmu.local", "Exported run report", "2026-09-19T11:30:00+00:00"),
]


def run_name(run_date: str) -> str:
    return f"{run_date} nightly"


def seed(conn: sqlite3.Connection) -> None:
    conn.executemany(
        "INSERT INTO users (email, name, role, password_hash) VALUES (?, ?, ?, ?)",
        [(u["email"], u["name"], u["role"], hash_password(u["password"])) for u in SEED_USERS],
    )
    conn.executemany(
        "INSERT INTO test_cases (title, module, priority, created_at, updated_at)"
        " VALUES (?, ?, ?, ?, ?)",
        [(t, m, p, SEED_TIME, SEED_TIME) for t, m, p in SEED_TEST_CASES],
    )
    conn.executemany(
        "INSERT INTO runs (name, run_date, total, passed, failed) VALUES (?, ?, ?, ?, ?)",
        [(run_name(d), d, total, passed, total - passed) for d, total, passed in SEED_RUNS],
    )
    conn.executemany(
        "INSERT INTO flaky_tests (test_name, flips, last_seen) VALUES (?, ?, ?)", SEED_FLAKY_TESTS
    )
    conn.executemany(
        "INSERT INTO activity (user_email, action, at) VALUES (?, ?, ?)", SEED_ACTIVITY
    )


def reset_database() -> None:
    """Drop every table and reload the seed data."""
    conn = sqlite3.connect(settings.db_path)
    try:
        db.recreate_schema(conn)
        seed(conn)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    reset_database()
    print(f"Database reset: {settings.db_path}")
