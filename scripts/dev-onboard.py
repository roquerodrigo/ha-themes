"""Onboard the local development Home Assistant and print browser login tokens."""

import json
import secrets
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = "http://localhost:8123"
CLIENT_ID = f"{BASE_URL}/"
CREDENTIALS_FILE = Path(__file__).resolve().parent.parent / "dev" / "credentials.env"
USERNAME = "themelab"


def post_json(path: str, payload: dict, access_token: str | None = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    request = urllib.request.Request(
        BASE_URL + path, data=json.dumps(payload).encode(), headers=headers
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read() or b"{}")


def exchange_code(code: str) -> dict:
    body = urllib.parse.urlencode(
        {"grant_type": "authorization_code", "code": code, "client_id": CLIENT_ID}
    ).encode()
    with urllib.request.urlopen(BASE_URL + "/auth/token", data=body) as response:
        return json.loads(response.read())


def main() -> None:
    password = secrets.token_urlsafe(12)
    created = post_json(
        "/api/onboarding/users",
        {
            "client_id": CLIENT_ID,
            "name": "Theme Lab",
            "username": USERNAME,
            "password": password,
            "language": "en",
        },
    )
    CREDENTIALS_FILE.write_text(
        f"HA_DEV_URL={BASE_URL}\nHA_DEV_USERNAME={USERNAME}\nHA_DEV_PASSWORD={password}\n"
    )
    tokens = exchange_code(created["auth_code"])
    access_token = tokens["access_token"]
    post_json("/api/onboarding/core_config", {}, access_token)
    post_json("/api/onboarding/analytics", {}, access_token)
    post_json(
        "/api/onboarding/integration",
        {"client_id": CLIENT_ID, "redirect_uri": f"{BASE_URL}/?auth_callback=1"},
        access_token,
    )
    tokens.update(
        hassUrl=BASE_URL,
        clientId=CLIENT_ID,
        expires=int(time.time() * 1000) + tokens["expires_in"] * 1000,
    )
    print(json.dumps(tokens))


if __name__ == "__main__":
    main()
