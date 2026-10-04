"""Diagnostics payload returned for a config entry."""

from __future__ import annotations

from typing import TypedDict


class HaThemesDiagnosticsPayload(TypedDict):
    """What HA Themes reports in its diagnostics download."""

    installed_themes: list[str]
    loaded_themes: list[str]
    themes_directory: str
    frontend_module_url: str
