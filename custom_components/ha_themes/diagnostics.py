"""Diagnostics support for ha_themes."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import HaThemesConfigEntry, HaThemesDiagnosticsPayload


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,  # noqa: ARG001 -- part of the signature Home Assistant calls
    entry: HaThemesConfigEntry,
) -> HaThemesDiagnosticsPayload:
    """Report which themes are installed and whether the frontend loads them."""
    runtime = entry.runtime_data
    return {
        "installed_themes": list(runtime.installed_themes),
        "loaded_themes": sorted(
            set(runtime.installed_themes) & runtime.theme_installer.loaded_themes
        ),
        "themes_directory": str(runtime.theme_installer.target_directory),
        "frontend_module_url": runtime.frontend_module.url or "",
    }
