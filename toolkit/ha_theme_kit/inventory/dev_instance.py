import json
import logging
import time
import urllib.parse
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from ha_theme_kit.inventory.local_theme_selection import LocalThemeSelection

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CREDENTIALS_FILE = PROJECT_ROOT / "dev" / "credentials.env"
NAVIGATION_ATTEMPTS = 3
INTERRUPTED_NAVIGATION = "is interrupted by another navigation"
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class DevInstance:
    url: str
    username: str
    password: str

    @classmethod
    def from_credentials_file(cls, path: Path = CREDENTIALS_FILE) -> DevInstance:
        values = dict(line.split("=", 1) for line in path.read_text().splitlines() if "=" in line)
        return cls(values["HA_DEV_URL"], values["HA_DEV_USERNAME"], values["HA_DEV_PASSWORD"])

    @property
    def client_id(self) -> str:
        return f"{self.url}/"

    def _post(self, path: str, payload: dict) -> dict:
        request = urllib.request.Request(
            self.url + path,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read())

    def login(self) -> dict:
        flow = self._post(
            "/auth/login_flow",
            {
                "client_id": self.client_id,
                "handler": ["homeassistant", None],
                "redirect_uri": f"{self.url}/?auth_callback=1",
            },
        )
        result = self._post(
            f"/auth/login_flow/{flow['flow_id']}",
            {"client_id": self.client_id, "username": self.username, "password": self.password},
        )
        body = urllib.parse.urlencode(
            {
                "grant_type": "authorization_code",
                "code": result["result"],
                "client_id": self.client_id,
            }
        ).encode()
        with urllib.request.urlopen(self.url + "/auth/token", data=body) as response:
            tokens = json.loads(response.read())
        tokens.update(
            hassUrl=self.url,
            clientId=self.client_id,
            expires=int(time.time() * 1000) + tokens["expires_in"] * 1000,
        )
        return tokens


@contextmanager
def chrome_session(instance: DevInstance, width: int = 1400, height: int = 900):
    """Yield a logged-in page of the installed Google Chrome, using an isolated profile.

    Themes applied with `open_with_theme` stay inside the page; on exit the last tested theme
    is saved to the user's profile with dark mode on automatic, for manual testing. When the
    session body fails, a failing restore is logged so the original error still propagates.
    """
    tokens = json.dumps(instance.login())
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": width, "height": height})
        local_selection = LocalThemeSelection()
        local_selection.attach(page)
        LOCAL_SELECTIONS[id(page)] = local_selection
        page.goto(f"{instance.url}/onboarding.html")
        page.evaluate(
            """tokens => {
                localStorage.setItem("hassTokens", tokens);
                localStorage.setItem("selectedLanguage", JSON.stringify("en"));
            }""",
            tokens,
        )
        # The onboarding page sends a finished instance to "/" on its own, which would otherwise
        # replace the first page the session opens.
        _goto_when_settled(page, f"{instance.url}/")
        _wait_for_app(page)
        try:
            yield page
        except BaseException:
            _restore_after_failure(page, instance, local_selection)
            raise
        else:
            _leave_in_automatic_mode(page, instance, local_selection)
        finally:
            LOCAL_SELECTIONS.pop(id(page), None)
            browser.close()


LOCAL_SELECTIONS: dict[int, LocalThemeSelection] = {}
SELECTION_SCRIPT = """({ theme, dark }) => document.querySelector("home-assistant").dispatchEvent(
    new CustomEvent("settheme", { detail: { theme, dark: dark ?? undefined } })
)"""
APPLIED_SELECTION_SCRIPT = """({ theme, dark }) => {
    const hass = document.querySelector("home-assistant")?.hass;
    return (hass?.selectedTheme?.theme || "default") === theme
        && hass.themes?.theme === theme
        && hass.themes?.darkMode === dark;
}"""


def _wait_for_app(page: Page) -> None:
    page.wait_for_function(
        "() => !document.getElementById('ha-launch-screen')"
        " && document.querySelector('home-assistant')?.shadowRoot"
        "?.querySelector('home-assistant-main')",
        timeout=60000,
    )


def _goto_when_settled(page: Page, url: str) -> None:
    for attempt in range(1, NAVIGATION_ATTEMPTS + 1):
        try:
            page.goto(url, wait_until="domcontentloaded")
            return
        except PlaywrightError as error:
            if INTERRUPTED_NAVIGATION not in error.message or attempt == NAVIGATION_ATTEMPTS:
                raise
            page.wait_for_load_state("domcontentloaded")


def _restore_after_failure(
    page: Page, instance: DevInstance, local_selection: LocalThemeSelection
) -> None:
    try:
        _leave_in_automatic_mode(page, instance, local_selection)
    except Exception:
        LOGGER.warning(
            "could not leave the dev instance with dark mode on automatic", exc_info=True
        )


def _leave_in_automatic_mode(
    page: Page, instance: DevInstance, local_selection: LocalThemeSelection
) -> None:
    tested_theme = (local_selection.selection or {}).get("theme")
    local_selection.persist = True
    _goto_when_settled(page, f"{instance.url}/theme-lab/0")
    _wait_for_app(page)
    theme = (
        tested_theme
        if tested_theme not in (None, "default")
        else page.evaluate(
            "() => document.querySelector('home-assistant').hass.selectedTheme?.theme || 'default'"
        )
    )
    page.evaluate(SELECTION_SCRIPT, {"theme": theme, "dark": None})
    page.evaluate(
        "theme => localStorage.setItem('selectedTheme', JSON.stringify({ theme }))", theme
    )
    page.wait_for_timeout(1500)


def open_with_theme(page: Page, url: str, theme: str, dark: bool, settle_ms: int = 4000) -> None:
    """Load `url` with the theme and mode applied from boot, and fail if the app shows another."""
    selection = {"theme": theme, "dark": dark}
    LOCAL_SELECTIONS[id(page)].selection = selection
    page.evaluate(
        "selection => localStorage.setItem('selectedTheme', JSON.stringify(selection))",
        selection,
    )
    _goto_when_settled(page, url)
    _wait_for_app(page)
    try:
        page.wait_for_function(APPLIED_SELECTION_SCRIPT, arg=selection, timeout=10000)
    except PlaywrightTimeoutError as error:
        applied = page.evaluate(
            """() => {
                const hass = document.querySelector("home-assistant").hass;
                return { selected: hass.selectedTheme, themes: hass.themes?.theme,
                         dark: hass.themes?.darkMode };
            }"""
        )
        raise RuntimeError(f"{url} did not apply {selection}: {applied}") from error
    page.wait_for_timeout(settle_ms)
