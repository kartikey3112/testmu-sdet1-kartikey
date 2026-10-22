"""Login: automated from generated/login.json (accepted prompt v4).

Each test is linked to its generated case with @pytest.mark.case. Expected results are taken
from the case; where the automation had to adapt a step, the test docstring says so.
"""

import re

import pytest
from playwright.sync_api import BrowserContext, Page, Response, expect

from framework.config import credentials
from framework.pages import DashboardPage, ForgotPasswordPage, LoginPage, ResetPasswordPage
from framework.test_control import TestControl

INVALID = "Invalid email or password."
LOCKED = "Your account is locked after too many failed sign-in attempts. Try again later."
FORGOT_SENT = "If an account exists for that email, we've sent a password reset link."
RESET_INVALID = "This reset link is invalid or has expired."
LOCKOUT_THRESHOLD = 5
SESSION_TTL_SECONDS = 1800
RESET_TOKEN_SECONDS = 30 * 60
LOCKOUT_SECONDS = 15 * 60


def submit_login(page: Page, email: str, password: str) -> Response:
    """Submit the login form and return the response to the POST itself (before redirects)."""
    login = LoginPage(page)
    with page.expect_response(
        lambda r: r.request.method == "POST" and r.url.endswith("/login")
    ) as info:
        login.login(email, password)
    return info.value


def fail_login(page: Page, email: str, times: int) -> Response:
    response = None
    for _ in range(times):
        LoginPage(page).open()
        response = submit_login(page, email, "wrong-password")
    return response


def session_cookie(context: BrowserContext) -> dict:
    return next(c for c in context.cookies() if c["name"] == "session")


# --- valid login -------------------------------------------------------------------------------

@pytest.mark.case("LOGIN-001")
def test_admin_signs_in_with_correct_credentials(page: Page) -> None:
    admin = credentials("admin")
    LoginPage(page).open()

    response = submit_login(page, admin.email, admin.password)

    assert response.status == 303
    assert response.headers["location"] == "/dashboard"
    cookie = session_cookie(page.context)
    assert cookie["httpOnly"] is True
    assert cookie["sameSite"] == "Lax"
    expect(DashboardPage(page).user_role).to_have_text("admin")


# --- invalid credentials -----------------------------------------------------------------------

@pytest.mark.case("LOGIN-004")
def test_correct_password_still_works_after_a_failed_attempt(page: Page) -> None:
    viewer = credentials("viewer")
    login = LoginPage(page).open()

    first = submit_login(page, viewer.email, "bad")
    expect(login.error).to_have_text(INVALID)
    second = submit_login(page, viewer.email, viewer.password)

    assert first.status == 401
    assert second.status == 303
    assert second.headers["location"] == "/dashboard"
    expect(DashboardPage(page).user_role).to_have_text("viewer")


@pytest.mark.case("LOGIN-005")
def test_unknown_email_gets_generic_error(page: Page) -> None:
    login = LoginPage(page).open()

    response = submit_login(page, "unknown@example.com", "any")

    assert response.status == 401
    expect(login.error).to_have_text(INVALID)


# --- forgot password ---------------------------------------------------------------------------

@pytest.mark.case("LOGIN-006")
def test_reset_link_sets_a_new_password(page: Page, test_control: TestControl) -> None:
    viewer = credentials("viewer")
    new_password = "newStrongPass1"
    ForgotPasswordPage(page).open().request_reset(viewer.email)
    link = test_control.latest_reset_link(viewer.email)

    reset = ResetPasswordPage(page).open(link)
    with page.expect_response(
        lambda r: r.request.method == "POST" and "/reset-password" in r.url
    ) as info:
        reset.set_password(new_password)

    assert info.value.status == 303
    assert info.value.headers["location"] == "/login?reason=reset"
    expect(LoginPage(page).notice).to_have_text("Your password has been updated. Please sign in.")
    signed_in = submit_login(page, viewer.email, new_password)
    assert signed_in.status == 303
    assert signed_in.headers["location"] == "/dashboard"


@pytest.mark.case("LOGIN-007")
def test_reset_link_is_expired_at_exactly_30_minutes(
    page: Page, test_control: TestControl
) -> None:
    admin = credentials("admin")
    ForgotPasswordPage(page).open().request_reset(admin.email)
    link = test_control.latest_reset_link(admin.email)

    test_control.advance_clock(RESET_TOKEN_SECONDS)
    response = page.goto(link)

    assert response.status == 400
    reset = ResetPasswordPage(page)
    expect(reset.error).to_have_text(RESET_INVALID)
    expect(reset.password).to_have_count(0)


@pytest.mark.case("LOGIN-008")
def test_forgot_password_does_not_reveal_unknown_email(
    page: Page, test_control: TestControl
) -> None:
    email = "nonexistent@testmu.local"
    forgot = ForgotPasswordPage(page).open()

    forgot.request_reset(email)

    expect(forgot.confirmation).to_have_text(FORGOT_SENT)
    assert test_control.outbox(to=email) == []


# --- session expiry ----------------------------------------------------------------------------

@pytest.mark.case("LOGIN-009")
def test_active_session_gives_access_to_dashboard(page: Page) -> None:
    admin = credentials("admin")
    LoginPage(page).open()
    submit_login(page, admin.email, admin.password)

    response = page.goto(DashboardPage.PATH)

    assert response.status == 200
    expect(DashboardPage(page).user_role).to_have_text("admin")


@pytest.mark.case("LOGIN-010")
def test_session_is_expired_at_exactly_1800_seconds(
    page: Page, test_control: TestControl
) -> None:
    viewer = credentials("viewer")
    LoginPage(page).open()
    submit_login(page, viewer.email, viewer.password)
    # Let the dashboard finish loading first. Otherwise a widget request still in flight can
    # hit the expired session, which deletes it, and the goto below sees "no session" and
    # redirects without ?reason=expired. (This was flaky, about 2 runs in 3, before the wait.)
    dashboard = DashboardPage(page)
    for widget in (dashboard.total_test_cases, dashboard.pass_rate, dashboard.recent_runs):
        widget.wait_loaded()

    test_control.advance_clock(SESSION_TTL_SECONDS)
    with page.expect_response(lambda r: r.url.endswith(DashboardPage.PATH)) as info:
        page.goto(DashboardPage.PATH)

    assert info.value.status == 303
    assert info.value.headers["location"] == "/login?reason=expired"
    expect(page).to_have_url(re.compile(r"/login\?reason=expired$"))
    expect(LoginPage(page).notice).to_have_text("Your session has expired. Please sign in again.")


# --- brute-force lockout -----------------------------------------------------------------------

@pytest.mark.case("LOGIN-012")
def test_fifth_consecutive_failure_locks_the_account(page: Page) -> None:
    admin = credentials("admin")

    fourth = fail_login(page, admin.email, LOCKOUT_THRESHOLD - 1)
    fifth = fail_login(page, admin.email, 1)

    assert fourth.status == 401
    assert fifth.status == 423
    expect(LoginPage(page).error).to_have_text(LOCKED)


@pytest.mark.case("LOGIN-013")
def test_correct_password_is_refused_while_locked(page: Page) -> None:
    viewer = credentials("viewer")
    fail_login(page, viewer.email, LOCKOUT_THRESHOLD)

    LoginPage(page).open()
    response = submit_login(page, viewer.email, viewer.password)

    assert response.status == 423
    expect(LoginPage(page).error).to_have_text(LOCKED)


@pytest.mark.case("LOGIN-014")
def test_lock_has_run_out_at_exactly_15_minutes(page: Page, test_control: TestControl) -> None:
    admin = credentials("admin")
    fail_login(page, admin.email, LOCKOUT_THRESHOLD)

    test_control.advance_clock(LOCKOUT_SECONDS)
    LoginPage(page).open()
    response = submit_login(page, admin.email, admin.password)

    assert response.status == 303
    assert response.headers["location"] == "/dashboard"
    expect(DashboardPage(page).user_role).to_have_text("admin")
