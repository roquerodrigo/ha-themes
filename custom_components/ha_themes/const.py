"""Constants for ha_themes."""

from __future__ import annotations

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "ha_themes"

THEMES_DIRECTORY = "themes"
STATIC_URL_PATH = f"/{DOMAIN}"
FRONTEND_MODULE_FILENAME = "ha-themes.js"

ISSUE_THEMES_NOT_LOADED = "themes_not_loaded"
