import logging
from contextlib import contextmanager

import pytest
from playwright.sync_api import Error as PlaywrightError

from ha_theme_kit.inventory import dev_instance
from ha_theme_kit.inventory.dev_instance import DevInstance, chrome_session

INSTANCE = DevInstance("http://localhost:8123", "dev", "dev")
INTERRUPTED = PlaywrightError(
    "Navigation to http://localhost:8123/lovelace/0 is interrupted by another navigation"
)


class FakePage:
    def __init__(self, goto_failures: list[Exception | None] | None = None) -> None:
        self.goto_failures = list(goto_failures or [])
        self.visited: list[str] = []
        self.settle_waits = 0

    def route_web_socket(self, url, handler) -> None:
        pass

    def goto(self, url: str, wait_until: str | None = None) -> None:
        self.visited.append(url)
        if self.goto_failures and (failure := self.goto_failures.pop(0)):
            raise failure

    def wait_for_load_state(self, state: str) -> None:
        self.settle_waits += 1

    def evaluate(self, script: str, argument=None) -> None:
        pass

    def wait_for_function(self, script: str, arg=None, timeout: int | None = None) -> None:
        pass

    def wait_for_timeout(self, milliseconds: int) -> None:
        pass


class FakeBrowser:
    def __init__(self, page: FakePage) -> None:
        self.page = page
        self.closed = False

    def new_page(self, viewport) -> FakePage:
        return self.page

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def browser(monkeypatch) -> FakeBrowser:
    fake_browser = FakeBrowser(FakePage())

    class FakeChromium:
        def launch(self, channel: str) -> FakeBrowser:
            return fake_browser

    class FakePlaywright:
        chromium = FakeChromium()

    @contextmanager
    def fake_sync_playwright():
        yield FakePlaywright()

    monkeypatch.setattr(dev_instance, "sync_playwright", fake_sync_playwright)
    monkeypatch.setattr(DevInstance, "login", lambda self: {"access_token": "token"})
    return fake_browser


@pytest.fixture
def failing_restore(monkeypatch) -> None:
    def fail(page, instance, local_selection) -> None:
        raise RuntimeError("restore failed")

    monkeypatch.setattr(dev_instance, "_leave_in_automatic_mode", fail)


@pytest.mark.usefixtures("failing_restore")
def test_a_failing_restore_is_logged_and_the_session_error_propagates(browser, caplog):
    with (
        caplog.at_level(logging.WARNING, logger=dev_instance.__name__),
        pytest.raises(ValueError, match="session failed"),
        chrome_session(INSTANCE),
    ):
        raise ValueError("session failed")

    assert "dark mode on automatic" in caplog.text
    assert "restore failed" in caplog.text
    assert browser.closed
    assert not dev_instance.LOCAL_SELECTIONS


@pytest.mark.usefixtures("failing_restore")
def test_a_failing_restore_after_a_successful_session_is_raised(browser):
    with pytest.raises(RuntimeError, match="restore failed"), chrome_session(INSTANCE):
        pass

    assert browser.closed
    assert not dev_instance.LOCAL_SELECTIONS


def test_navigation_is_retried_once_the_interrupting_navigation_settles():
    page = FakePage(goto_failures=[INTERRUPTED])

    dev_instance._goto_when_settled(page, "http://localhost:8123/lovelace/0")

    assert len(page.visited) == 2
    assert page.settle_waits == 1


def test_navigation_gives_up_after_the_last_attempt():
    page = FakePage(goto_failures=[INTERRUPTED] * dev_instance.NAVIGATION_ATTEMPTS)

    with pytest.raises(PlaywrightError, match="interrupted"):
        dev_instance._goto_when_settled(page, "http://localhost:8123/lovelace/0")

    assert len(page.visited) == dev_instance.NAVIGATION_ATTEMPTS


def test_other_navigation_errors_are_not_retried():
    page = FakePage(goto_failures=[PlaywrightError("net::ERR_CONNECTION_REFUSED")])

    with pytest.raises(PlaywrightError, match="ERR_CONNECTION_REFUSED"):
        dev_instance._goto_when_settled(page, "http://localhost:8123/lovelace/0")

    assert len(page.visited) == 1


def test_opening_with_a_theme_waits_out_the_redirect_of_the_login_page(monkeypatch):
    page = FakePage(goto_failures=[INTERRUPTED])
    monkeypatch.setitem(dev_instance.LOCAL_SELECTIONS, id(page), dev_instance.LocalThemeSelection())

    dev_instance.open_with_theme(page, "http://localhost:8123/lovelace/0", "Anthropic", dark=False)

    assert page.visited == ["http://localhost:8123/lovelace/0"] * 2
    assert page.settle_waits == 1


def test_the_session_opens_once_the_login_page_has_sent_it_to_the_app(browser):
    browser.page.goto_failures = [None, INTERRUPTED]

    with chrome_session(INSTANCE) as page:
        assert page.visited == [
            f"{INSTANCE.url}/onboarding.html",
            f"{INSTANCE.url}/",
            f"{INSTANCE.url}/",
        ]
