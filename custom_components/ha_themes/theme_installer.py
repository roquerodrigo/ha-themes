"""Installs the packaged themes where Home Assistant loads themes from."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from homeassistant.components.frontend import DATA_THEMES
from homeassistant.components.frontend import DOMAIN as FRONTEND_DOMAIN
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import issue_registry
from homeassistant.util.yaml import load_yaml_dict

from .const import DOMAIN, ISSUE_THEMES_NOT_LOADED, LOGGER, THEMES_DIRECTORY

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

PACKAGED_THEMES = Path(__file__).parent / THEMES_DIRECTORY
RELOAD_THEMES_SERVICE = "reload_themes"


class HaThemesThemeInstaller:
    """
    Copies the packaged theme files into `<config>/themes/ha_themes/`.

    Home Assistant only loads themes from the `frontend: themes:` YAML and replaces
    anything else on every `frontend.reload_themes`, so the themes are installed as
    files the standard `!include_dir_merge_named themes` picks up, then reloaded. When
    the configuration does not include that directory a repair issue explains the fix.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Bind the installer to a Home Assistant instance."""
        self._hass = hass

    @property
    def target_directory(self) -> Path:
        """Directory the themes are installed into."""
        return Path(self._hass.config.path(THEMES_DIRECTORY, DOMAIN))

    @property
    def loaded_themes(self) -> frozenset[str]:
        """Names of the themes the frontend currently serves."""
        themes = self._hass.data.get(DATA_THEMES)
        return frozenset(themes) if themes else frozenset()

    async def async_install(self) -> tuple[str, ...]:
        """Install or update the theme files and reload the frontend themes."""
        installed = await self._hass.async_add_executor_job(self._synchronize_files)
        await self._async_reload_themes()
        self._update_issue(installed)
        LOGGER.debug("Installed themes %s into %s", installed, self.target_directory)
        return installed

    async def async_uninstall(self) -> None:
        """Remove the installed theme files and reload the frontend themes."""
        await self._hass.async_add_executor_job(self._remove_files)
        await self._async_reload_themes()
        issue_registry.async_delete_issue(self._hass, DOMAIN, ISSUE_THEMES_NOT_LOADED)

    def _remove_files(self) -> None:
        """Delete the installed theme directory, if present."""
        shutil.rmtree(self.target_directory, ignore_errors=True)

    def _synchronize_files(self) -> tuple[str, ...]:
        """Mirror the packaged theme files and return the theme names they define."""
        self.target_directory.mkdir(parents=True, exist_ok=True)
        packaged = {source.name: source for source in PACKAGED_THEMES.glob("*.yaml")}
        for stale in self.target_directory.glob("*.yaml"):
            if stale.name not in packaged:
                stale.unlink()
        names: list[str] = []
        for name, source in sorted(packaged.items()):
            content = source.read_bytes()
            target = self.target_directory / name
            if not target.is_file() or target.read_bytes() != content:
                target.write_bytes(content)
            names.extend(str(theme) for theme in load_yaml_dict(source))
        return tuple(names)

    async def _async_reload_themes(self) -> None:
        """Ask the frontend to re-read the themes from the configuration."""
        try:
            await self._hass.services.async_call(
                FRONTEND_DOMAIN, RELOAD_THEMES_SERVICE, blocking=True
            )
        except HomeAssistantError as error:
            LOGGER.warning("Failed to reload themes: %s", error)

    def _update_issue(self, installed: tuple[str, ...]) -> None:
        """Raise a repair issue while the installed themes are not being loaded."""
        if set(installed) <= self.loaded_themes:
            issue_registry.async_delete_issue(
                self._hass, DOMAIN, ISSUE_THEMES_NOT_LOADED
            )
            return
        issue_registry.async_create_issue(
            self._hass,
            DOMAIN,
            ISSUE_THEMES_NOT_LOADED,
            is_fixable=False,
            severity=issue_registry.IssueSeverity.WARNING,
            translation_key=ISSUE_THEMES_NOT_LOADED,
            translation_placeholders={
                "directory": f"{THEMES_DIRECTORY}/{DOMAIN}",
                "configuration": (
                    "frontend:\n  themes: !include_dir_merge_named themes"
                ),
            },
        )
