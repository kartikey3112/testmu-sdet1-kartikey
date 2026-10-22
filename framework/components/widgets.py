"""Dashboard widget components exposing wait_loaded() and value()."""

from playwright.sync_api import Locator, expect


class Widget:
    """One dashboard widget. Its root element carries data-state = loading | loaded | error."""

    def __init__(self, root: Locator) -> None:
        self.root = root

    @property
    def state(self) -> str | None:
        return self.root.get_attribute("data-state")

    @property
    def error(self) -> Locator:
        return self.root.get_by_test_id("widget-error")

    def wait_loaded(self) -> "Widget":
        expect(self.root).to_have_attribute("data-state", "loaded")
        return self

    def wait_error(self) -> "Widget":
        expect(self.root).to_have_attribute("data-state", "error")
        return self

    def value(self) -> str:
        """Displayed value of a single-number widget, after it has loaded."""
        self.wait_loaded()
        return self.root.get_by_test_id("widget-value").inner_text()


class RecentRunsWidget(Widget):
    @property
    def rows(self) -> Locator:
        return self.root.get_by_test_id("run-row")

    @property
    def empty_message(self) -> Locator:
        return self.root.get_by_test_id("runs-empty")

    def filter_status(self, status: str) -> None:
        self.root.get_by_test_id("runs-filter-status").select_option(status)

    def filter_dates(self, date_from: str = "", date_to: str = "") -> None:
        self.root.get_by_test_id("runs-filter-from").fill(date_from)
        self.root.get_by_test_id("runs-filter-to").fill(date_to)

    def sort_by(self, sort: str, order: str = "desc") -> None:
        self.root.get_by_test_id("runs-sort").select_option(sort)
        self.root.get_by_test_id("runs-order").select_option(order)

    def run_ids(self) -> list[int]:
        self.wait_loaded()
        return [int(v) for v in self.rows.evaluate_all("rows => rows.map(r => r.dataset.runId)")]

    def column(self, testid: str) -> list[str]:
        self.wait_loaded()
        return self.rows.get_by_test_id(testid).all_inner_texts()


class ListWidget(Widget):
    """Widget showing a list of items (flaky tests, team activity)."""

    def __init__(self, root: Locator, item_testid: str) -> None:
        super().__init__(root)
        self.items = root.get_by_test_id(item_testid)
