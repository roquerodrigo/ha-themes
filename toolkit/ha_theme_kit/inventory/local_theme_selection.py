import json
from typing import Any

from playwright.sync_api import Page, WebSocketRoute

THEME_KEY = "theme"
WEBSOCKET_URL = "**/api/websocket"


class LocalThemeSelection:
    """Keep a page's theme selection inside the page instead of the user's server-side profile.

    Home Assistant saves the selection as frontend user data and pushes every change to all
    sessions of the same user, so browser sessions running side by side would switch each
    other's theme. Routing the page's websocket answers the selection locally; `persist`
    turns the routing off so the selection reaches the server again.
    """

    def __init__(self) -> None:
        self.selection: dict[str, Any] | None = None
        self.persist = False

    def attach(self, page: Page) -> None:
        page.route_web_socket(WEBSOCKET_URL, self._route)

    def _route(self, page_socket: WebSocketRoute) -> None:
        server_socket = page_socket.connect_to_server()
        tracked_requests: dict[int, str | None] = {}

        def from_page(message: str | bytes) -> None:
            forwarded, replies = self.handle_page_message(message, tracked_requests)
            if forwarded is not None:
                server_socket.send(forwarded)
            for reply in replies:
                page_socket.send(reply)

        def from_server(message: str | bytes) -> None:
            page_socket.send(self.handle_server_message(message, tracked_requests))

        page_socket.on_message(from_page)
        server_socket.on_message(from_server)

    def handle_page_message(
        self, message: str | bytes, tracked_requests: dict[int, str | None]
    ) -> tuple[str | bytes | None, list[str]]:
        command = _decode(message)
        if self.persist or not isinstance(command, dict):
            return message, []
        command_type = command.get("type")
        key = command.get("key")
        if command_type == "frontend/set_user_data" and key == THEME_KEY:
            self.selection = command.get("value")
            replies = [_result(command["id"], None)]
            replies += [
                self._event(request_id, request_key)
                for request_id, request_key in tracked_requests.items()
                if request_key in (THEME_KEY, None)
            ]
            return None, replies
        if command_type == "frontend/get_user_data" and key == THEME_KEY and self.selection:
            return None, [_result(command["id"], {"value": self.selection})]
        if command_type in ("frontend/subscribe_user_data", "frontend/get_user_data") and (
            key in (THEME_KEY, None)
        ):
            tracked_requests[command["id"]] = key
        return message, []

    def handle_server_message(
        self, message: str | bytes, tracked_requests: dict[int, str | None]
    ) -> str | bytes:
        if self.persist or self.selection is None:
            return message
        payload = _decode(message)
        replies = payload if isinstance(payload, list) else [payload]
        changed = False
        for reply in replies:
            if isinstance(reply, dict) and reply.get("id") in tracked_requests:
                changed = self._rewrite(reply, tracked_requests) or changed
        return json.dumps(payload) if changed else message

    def _rewrite(self, reply: dict[str, Any], tracked_requests: dict[int, str | None]) -> bool:
        key = tracked_requests[reply["id"]]
        container = reply.get("event") if reply.get("type") == "event" else reply.get("result")
        if not isinstance(container, dict) or "value" not in container:
            return False
        container["value"] = self._value_for(key, container["value"])
        if reply.get("type") == "result":
            del tracked_requests[reply["id"]]
        return True

    def _value_for(self, key: str | None, value: Any) -> Any:
        if key == THEME_KEY:
            return self.selection
        return {**(value or {}), THEME_KEY: self.selection}

    def _event(self, request_id: int, key: str | None) -> str:
        return json.dumps(
            {"id": request_id, "type": "event", "event": {"value": self._value_for(key, {})}}
        )


def _result(request_id: int, result: Any) -> str:
    return json.dumps({"id": request_id, "type": "result", "success": True, "result": result})


def _decode(message: str | bytes) -> Any:
    try:
        return json.loads(message)
    except ValueError:
        return None
