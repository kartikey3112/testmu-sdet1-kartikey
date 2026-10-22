"""DashboardPage page object."""

from urllib.parse import urlencode

from playwright.sync_api import Page

from framework.components.widgets import ListWidget, RecentRunsWidget, Widget


class DashboardPage:
    PATH = "/dashboard"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.sidebar = page.get_by_test_id("sidebar")
        self.menu_toggle = page.get_by_test_id("menu-toggle")
        self.user_role = page.get_by_test_id("user-role")
        self.logout_button = page.get_by_test_id("logout")
        self.widget_grid = page.get_by_test_id("widget-grid")

        self.total_test_cases = Widget(page.get_by_test_id("widget-total-test-cases"))
        self.pass_rate = Widget(page.get_by_test_id("widget-pass-rate"))
        self.recent_runs = RecentRunsWidget(page.get_by_test_id("widget-recent-runs"))
        self.flaky_tests = ListWidget(page.get_by_test_id("widget-flaky-tests"), "flaky-row")
        self.team_activity = ListWidget(
            page.get_by_test_id("widget-team-activity"), "activity-item"
        )

    def open(self, **query: str) -> "DashboardPage":
        self.page.goto(f"{self.PATH}?{urlencode(query)}" if query else self.PATH)
        return self

    def logout(self) -> None:
        self.logout_button.click()
