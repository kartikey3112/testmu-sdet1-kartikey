"""Smoke: the total-test-cases widget loads and agrees with the API and the seed data."""

import pytest
from playwright.sync_api import Page

from app.seed import SEED_TEST_CASES
from framework.api_client import ApiClient
from framework.pages import DashboardPage


@pytest.mark.smoke
def test_total_test_cases_widget_matches_api_and_seed(
    admin_page: Page, admin_api: ApiClient
) -> None:
    api_value = admin_api.widget("total-test-cases").json()["value"]

    ui_value = DashboardPage(admin_page).open().total_test_cases.value()

    assert int(ui_value) == api_value == len(SEED_TEST_CASES)
