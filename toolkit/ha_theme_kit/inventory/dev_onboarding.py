"""First-run setup of the local development instance: a test user and the integration."""

import json
import secrets
import urllib.parse
import urllib.request

from ha_theme_kit.inventory.dev_instance import CREDENTIALS_FILE, DevInstance

BASE_URL = "http://localhost:8123"
USERNAME = "themelab"


def _post(path: str, payload: dict, access_token: str | None = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    request = urllib.request.Request(
        BASE_URL + path, data=json.dumps(payload).encode(), headers=headers
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read() or b"{}")


def onboard() -> DevInstance:
    client_id = f"{BASE_URL}/"
    password = secrets.token_urlsafe(12)
    created = _post(
        "/api/onboarding/users",
        {
            "client_id": client_id,
            "name": "Theme Lab",
            "username": USERNAME,
            "password": password,
            "language": "en",
        },
    )
    CREDENTIALS_FILE.write_text(
        f"HA_DEV_URL={BASE_URL}\nHA_DEV_USERNAME={USERNAME}\nHA_DEV_PASSWORD={password}\n"
    )
    body = urllib.parse.urlencode(
        {"grant_type": "authorization_code", "code": created["auth_code"], "client_id": client_id}
    ).encode()
    with urllib.request.urlopen(BASE_URL + "/auth/token", data=body) as response:
        access_token = json.loads(response.read())["access_token"]
    _post("/api/onboarding/core_config", {}, access_token)
    _post("/api/onboarding/analytics", {}, access_token)
    _post(
        "/api/onboarding/integration",
        {"client_id": client_id, "redirect_uri": f"{BASE_URL}/?auth_callback=1"},
        access_token,
    )
    add_integration(access_token)
    return DevInstance.from_credentials_file()


def add_integration(access_token: str) -> dict:
    """Add the ha_themes integration through its config flow, as a user would."""
    flow = _post("/api/config/config_entries/flow", {"handler": "ha_themes"}, access_token)
    if flow.get("type") == "abort":
        return flow
    return _post(f"/api/config/config_entries/flow/{flow['flow_id']}", {}, access_token)
