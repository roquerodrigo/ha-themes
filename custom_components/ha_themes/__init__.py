"""HA Themes integration for Home Assistant."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .data import HaThemesData
from .frontend_module import HaThemesFrontendModule
from .theme_installer import HaThemesThemeInstaller

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import HaThemesConfigEntry


async def async_setup_entry(hass: HomeAssistant, entry: HaThemesConfigEntry) -> bool:
    """Install the themes and load the support module on every frontend page."""
    frontend_module = HaThemesFrontendModule(hass)
    await frontend_module.async_register()
    theme_installer = HaThemesThemeInstaller(hass)
    entry.runtime_data = HaThemesData(
        theme_installer=theme_installer,
        frontend_module=frontend_module,
        installed_themes=await theme_installer.async_install(),
    )
    return True


async def async_unload_entry(
    hass: HomeAssistant,  # noqa: ARG001 -- part of the signature Home Assistant calls
    entry: HaThemesConfigEntry,
) -> bool:
    """Stop loading the support module; installed themes stay until removal."""
    entry.runtime_data.frontend_module.unregister()
    return True


async def async_remove_entry(
    hass: HomeAssistant,
    entry: HaThemesConfigEntry,  # noqa: ARG001 -- part of the signature Home Assistant calls
) -> None:
    """Remove the installed theme files when the integration is deleted."""
    await HaThemesThemeInstaller(hass).async_uninstall()
