import json
import time
import urllib.parse
import urllib.request
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CREDENTIALS_FILE = PROJECT_ROOT / "dev" / "credentials.env"


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
    """Yield a logged-in page of the installed Google Chrome, using an isolated profile."""
    tokens = json.dumps(instance.login())
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(f"{instance.url}/onboarding.html")
        page.evaluate(
            """tokens => {
                localStorage.setItem("hassTokens", tokens);
                localStorage.setItem("selectedLanguage", JSON.stringify("en"));
            }""",
            tokens,
        )
        try:
            yield page
        finally:
            _leave_in_automatic_mode(page, instance)
            browser.close()


TESTED_THEMES: dict[int, str] = {}
SELECTION_SCRIPT = """({ theme, dark }) => document.querySelector("home-assistant").dispatchEvent(
    new CustomEvent("settheme", { detail: { theme, dark: dark ?? undefined } })
)"""


def _wait_for_app(page: Page) -> None:
    page.wait_for_function(
        "() => !document.getElementById('ha-launch-screen')"
        " && document.querySelector('home-assistant')?.shadowRoot"
        "?.querySelector('home-assistant-main')",
        timeout=60000,
    )


def _leave_in_automatic_mode(page: Page, instance: DevInstance) -> None:
    """Hand the instance back for manual testing: the last tested theme, dark mode on auto.

    The selection is saved to the user's profile on the server, so whatever a capture
    applied last would otherwise stick for the next person who opens the instance.
    """
    page.goto(f"{instance.url}/lovelace/0", wait_until="domcontentloaded")
    _wait_for_app(page)
    theme = TESTED_THEMES.pop(id(page), None) or page.evaluate(
        "() => document.querySelector('home-assistant').hass.selectedTheme?.theme || 'default'"
    )
    page.evaluate(SELECTION_SCRIPT, {"theme": theme, "dark": None})
    page.evaluate(
        "theme => localStorage.setItem('selectedTheme', JSON.stringify({ theme }))", theme
    )
    page.wait_for_timeout(1500)


def open_with_theme(page: Page, url: str, theme: str, dark: bool, settle_ms: int = 4000) -> None:
    """The frontend restores the selection from server-side user data after boot, overriding
    localStorage, so the theme is also applied through the app's own `settheme` event."""
    page.evaluate(
        "selection => localStorage.setItem('selectedTheme', JSON.stringify(selection))",
        {"theme": theme, "dark": dark},
    )
    page.goto(url, wait_until="domcontentloaded")
    _wait_for_app(page)
    page.evaluate(SELECTION_SCRIPT, {"theme": theme, "dark": dark})
    if theme != "default":
        TESTED_THEMES[id(page)] = theme
    page.wait_for_timeout(settle_ms)
