"""Registers the support module the themes rely on with the frontend."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

from homeassistant.components.frontend import add_extra_js_url, remove_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.util.hass_dict import HassKey

from .const import DOMAIN, FRONTEND_MODULE_FILENAME, STATIC_URL_PATH

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

FRONTEND_DIRECTORY = Path(__file__).parent / "frontend"

# Static routes cannot be removed from the running HTTP server, so whether the path is
# already registered is process-wide state that outlives any single config entry.
STATIC_PATH_REGISTERED: HassKey[bool] = HassKey(f"{DOMAIN}_static_path_registered")


class HaThemesFrontendModule:
    """
    Serves the support module and loads it on every frontend page.

    The module binds the page body to the theme font, loads web fonts and recolors
    generic integration icons. Its URL carries a content hash because both the HTTP
    cache and the frontend's service worker would otherwise keep serving old copies.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Bind the module to a Home Assistant instance."""
        self._hass = hass
        self._url: str | None = None

    @property
    def url(self) -> str | None:
        """URL the frontend loads the module from, once registered."""
        return self._url

    async def async_register(self) -> str:
        """Serve the module and add it to the frontend's extra modules."""
        if not self._hass.data.get(STATIC_PATH_REGISTERED):
            await self._hass.http.async_register_static_paths(
                [
                    StaticPathConfig(
                        STATIC_URL_PATH, str(FRONTEND_DIRECTORY), cache_headers=True
                    )
                ]
            )
            self._hass.data[STATIC_PATH_REGISTERED] = True
        digest = await self._hass.async_add_executor_job(self._content_digest)
        self._url = f"{STATIC_URL_PATH}/{FRONTEND_MODULE_FILENAME}?v={digest}"
        add_extra_js_url(self._hass, self._url)
        return self._url

    def unregister(self) -> None:
        """Stop loading the module on new frontend sessions."""
        if self._url is not None:
            remove_extra_js_url(self._hass, self._url)
            self._url = None

    @staticmethod
    def _content_digest() -> str:
        """Short hash of the module's content."""
        content = (FRONTEND_DIRECTORY / FRONTEND_MODULE_FILENAME).read_bytes()
        return hashlib.sha256(content).hexdigest()[:12]
