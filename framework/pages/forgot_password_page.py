"""ForgotPasswordPage page object, plus the reset page the emailed link opens."""

from playwright.sync_api import Page


class ForgotPasswordPage:
    PATH = "/forgot-password"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.email = page.get_by_test_id("forgot-email")
        self.submit = page.get_by_test_id("forgot-submit")
        self.confirmation = page.get_by_test_id("forgot-confirmation")

    def open(self) -> "ForgotPasswordPage":
        self.page.goto(self.PATH)
        return self

    def request_reset(self, email: str) -> None:
        self.email.fill(email)
        self.submit.click()


class ResetPasswordPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.password = page.get_by_test_id("reset-password")
        self.confirm_password = page.get_by_test_id("reset-confirm-password")
        self.submit = page.get_by_test_id("reset-submit")
        self.error = page.get_by_test_id("reset-error")

    def open(self, reset_link: str) -> "ResetPasswordPage":
        self.page.goto(reset_link)
        return self

    def set_password(self, password: str, confirm: str | None = None) -> None:
        self.password.fill(password)
        self.confirm_password.fill(password if confirm is None else confirm)
        self.submit.click()
