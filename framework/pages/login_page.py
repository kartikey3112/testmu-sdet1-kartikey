"""LoginPage page object."""

from playwright.sync_api import Locator, Page


class LoginPage:
    PATH = "/login"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.email = page.get_by_test_id("login-email")
        self.password = page.get_by_test_id("login-password")
        self.submit = page.get_by_test_id("login-submit")
        self.error: Locator = page.get_by_test_id("login-error")
        self.notice: Locator = page.get_by_test_id("login-notice")
        self.forgot_password_link = page.get_by_test_id("forgot-password-link")

    def open(self, reason: str | None = None) -> "LoginPage":
        self.page.goto(f"{self.PATH}?reason={reason}" if reason else self.PATH)
        return self

    def login(self, email: str, password: str) -> None:
        self.email.fill(email)
        self.password.fill(password)
        self.submit.click()
