"""Dashboard: automated from generated/dashboard.json (accepted prompt v3).

Not automated: DASH-010. Its title says "expired session" but its steps use a tampered cookie;
the app treats an unknown cookie as no session and redirects to /login without
?reason=expired, so the generated expectation is wrong (checked by running it as generated).
"""

import pytest
from playwright.sync_api import Page, expect

from framework.pages import DashboardPage
from tests.conftest import NewPage

ADMIN_WIDGETS = ["widget-total-test-cases", "widget-pass-rate", "widget-recent-runs",
                 "widget-flaky-tests", "widget-team-activity"]
VIEWER_WIDGETS = ADMIN_WIDGETS[:3]


# --- widget loading ----------------------------------------------------------------------------

@pytest.mark.case("DASH-001")
def test_total_test_cases_widget_loads(admin_page: Page) -> None:
    dashboard = DashboardPage(admin_page).open()

    expect(dashboard.total_test_cases.root).to_have_attribute("data-state", "loaded")


@pytest.mark.case("DASH-002")
def test_date_from_after_date_to_puts_recent_runs_in_error(admin_page: Page) -> None:
    runs = DashboardPage(admin_page).open().recent_runs
    runs.wait_loaded()

    runs.filter_dates(date_from="2026-09-20", date_to="2026-09-10")

    runs.wait_error()
    expect(runs.error).to_contain_text("date_from must be on or before date_to")


# --- data accuracy -----------------------------------------------------------------------------

@pytest.mark.case("DASH-004")
def test_total_test_cases_shows_seed_count(admin_page: Page) -> None:
    dashboard = DashboardPage(admin_page).open()

    assert dashboard.total_test_cases.value() == "24"


@pytest.mark.case("DASH-005")
def test_pass_rate_shows_latest_run(admin_page: Page) -> None:
    pass_rate = DashboardPage(admin_page).open().pass_rate

    assert pass_rate.value() == "87.5%"
    expect(pass_rate.root.get_by_test_id("widget-caption")).to_have_text("2026-09-21 nightly")


# --- filter/sort behavior ----------------------------------------------------------------------

@pytest.mark.case("DASH-007")
def test_recent_runs_default_is_latest_ten_newest_first(admin_page: Page) -> None:
    runs = DashboardPage(admin_page).open().recent_runs
    runs.wait_loaded()

    expect(runs.rows).to_have_count(10)
    expect(runs.rows.first.get_by_test_id("run-name")).to_have_text("2026-09-21 nightly")


@pytest.mark.case("DASH-009")
def test_same_day_date_range_returns_that_run(admin_page: Page) -> None:
    runs = DashboardPage(admin_page).open().recent_runs
    runs.wait_loaded()

    runs.filter_dates(date_from="2026-09-10", date_to="2026-09-10")

    expect(runs.rows).to_have_count(1)
    expect(runs.rows.first.get_by_test_id("run-name")).to_have_text("2026-09-10 nightly")


# --- responsive layout -------------------------------------------------------------------------

@pytest.mark.case("DASH-011")
def test_wide_viewport_shows_sidebar_and_two_columns(new_page: NewPage) -> None:
    page = new_page(role="admin", viewport={"width": 1024, "height": 800})
    dashboard = DashboardPage(page).open()
    dashboard.pass_rate.wait_loaded()

    expect(dashboard.sidebar).to_be_visible()
    expect(dashboard.menu_toggle).to_be_hidden()
    total = dashboard.total_test_cases.root.bounding_box()
    rate = dashboard.pass_rate.root.bounding_box()
    assert total["y"] == rate["y"], "total-test-cases and pass-rate should share a row"
    assert rate["x"] > total["x"]


@pytest.mark.case("DASH-013")
def test_narrow_viewport_hides_sidebar_behind_menu(new_page: NewPage) -> None:
    page = new_page(role="admin", viewport={"width": 500, "height": 900})
    dashboard = DashboardPage(page).open()

    expect(dashboard.menu_toggle).to_have_attribute("aria-expanded", "false")
    expect(dashboard.sidebar).to_be_hidden()
    dashboard.menu_toggle.click()
    expect(dashboard.menu_toggle).to_have_attribute("aria-expanded", "true")
    expect(dashboard.sidebar).to_be_visible()


# --- permission-based visibility ---------------------------------------------------------------

@pytest.mark.case("DASH-014")
def test_admin_sees_all_five_widgets(admin_page: Page) -> None:
    DashboardPage(admin_page).open()

    for testid in ADMIN_WIDGETS:
        expect(admin_page.get_by_test_id(testid)).to_have_count(1)


@pytest.mark.case("DASH-015")
def test_viewer_sees_only_three_widgets(viewer_page: Page) -> None:
    DashboardPage(viewer_page).open()

    for testid in VIEWER_WIDGETS:
        expect(viewer_page.get_by_test_id(testid)).to_have_count(1)
    for testid in ("widget-flaky-tests", "widget-team-activity"):
        expect(viewer_page.get_by_test_id(testid)).to_have_count(0)


@pytest.mark.case("DASH-016")
def test_viewer_gets_403_from_flaky_tests_endpoint(viewer_page: Page) -> None:
    DashboardPage(viewer_page).open()

    response = viewer_page.request.get("/api/v1/dashboard/flaky-tests")

    assert response.status == 403
    assert response.json() == {"error": {"code": "forbidden", "message": "Admin role required"}}
