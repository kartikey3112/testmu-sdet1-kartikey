"""Smoke: a user can sign in through the UI and lands on the dashboard."""

import re

import pytest
from playwright.sync_api import Page, expect

from framework.config import credentials
from framework.pages import DashboardPage, LoginPage


@pytest.mark.smoke
def test_admin_can_sign_in_and_reach_dashboard(page: Page) -> None:
    admin = credentials("admin")

    LoginPage(page).open().login(admin.email, admin.password)

    expect(page).to_have_url(re.compile(r"/dashboard$"))
    dashboard = DashboardPage(page)
    expect(dashboard.user_role).to_have_text("admin")
    expect(page.get_by_role("heading", name="Dashboard")).to_be_visible()
