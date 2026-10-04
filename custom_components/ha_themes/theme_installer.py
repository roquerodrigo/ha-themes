"""Installs the packaged themes where Home Assistant loads themes from."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from homeassistant.components.frontend import DATA_THEMES, EVENT_THEMES_UPDATED
from homeassistant.components.frontend import DOMAIN as FRONTEND_DOMAIN
from homeassistant.core import Event, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import issue_registry
from homeassistant.util.file import write_utf8_file_atomic
from homeassistant.util.yaml import load_yaml_dict

from .const import (
    DOMAIN,
    ISSUE_THEMES_NOT_LOADED,
    ISSUE_THEMES_RELOAD_FAILED,
    LOGGER,
    THEMES_DIRECTORY,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.core import CALLBACK_TYPE, HomeAssistant

PACKAGED_THEMES = Path(__file__).parent / THEMES_DIRECTORY
RELOAD_THEMES_SERVICE = "reload_themes"


class HaThemesThemeInstaller:
    """
    Copies the packaged theme files into `<config>/themes/ha_themes/`.

    Home Assistant only loads themes from the `frontend: themes:` YAML and replaces
    anything else on every `frontend.reload_themes`, so the themes are installed as
    files the standard `!include_dir_merge_named themes` picks up. The themes are
    reloaded only when a file changed or the frontend does not serve them yet. A
    repair issue explains the fix when the reload fails or the configuration does not
    include that directory, and is re-checked whenever the themes are reloaded.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Bind the installer to a Home Assistant instance."""
        self._hass = hass
        self._installed: tuple[str, ...] = ()

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
        """Install or update the theme files and reload the themes if needed."""
        files_changed = await self._hass.async_add_executor_job(self._synchronize_files)
        installed = await self._hass.async_add_executor_job(
            self._read_packaged_theme_names
        )
        self._installed = installed
        reload_error = None
        if files_changed or not set(installed) <= self.loaded_themes:
            reload_error = await self._async_reload_themes()
        self._update_issues(installed, reload_error)
        LOGGER.debug("Installed themes %s into %s", installed, self.target_directory)
        return installed

    async def async_uninstall(self) -> None:
        """Remove the installed theme files and reload the frontend themes."""
        await self._hass.async_add_executor_job(self._remove_files)
        await self._async_reload_themes()
        self.clear_issues()

    @callback
    def async_watch_theme_reloads(self) -> CALLBACK_TYPE:
        """Re-check the repair issues after every successful theme reload."""
        return self._hass.bus.async_listen(
            EVENT_THEMES_UPDATED, self._handle_themes_updated
        )

    @callback
    def clear_issues(self) -> None:
        """Remove the integration's repair issues."""
        self._delete_issue(ISSUE_THEMES_NOT_LOADED)
        self._delete_issue(ISSUE_THEMES_RELOAD_FAILED)

    @callback
    def _handle_themes_updated(self, _event: Event) -> None:
        """Update the repair issues against the themes the frontend now serves."""
        self._update_issues(self._installed, None)

    def _remove_files(self) -> None:
        """Delete the installed theme directory, if present."""
        if self.target_directory.exists():
            shutil.rmtree(self.target_directory, onexc=self._log_removal_failure)

    @staticmethod
    def _log_removal_failure(
        _function: Callable[..., object], path: str, error: BaseException
    ) -> None:
        """Report a file the uninstall could not delete instead of failing it."""
        LOGGER.warning("Could not remove %s: %s", path, error)

    def _synchronize_files(self) -> bool:
        """Mirror the packaged theme files and return whether any file changed."""
        self.target_directory.mkdir(parents=True, exist_ok=True)
        packaged = {source.name: source for source in PACKAGED_THEMES.glob("*.yaml")}
        files_changed = False
        for stale in self.target_directory.glob("*.yaml"):
            if stale.name not in packaged:
                stale.unlink()
                files_changed = True
                LOGGER.info(
                    "Removed %s: %s is managed by %s and only keeps its themes",
                    stale,
                    self.target_directory,
                    DOMAIN,
                )
        for name, source in sorted(packaged.items()):
            content = source.read_bytes()
            target = self.target_directory / name
            if not target.is_file() or target.read_bytes() != content:
                write_utf8_file_atomic(str(target), content, mode="wb")
                files_changed = True
        return files_changed

    @staticmethod
    def _read_packaged_theme_names() -> tuple[str, ...]:
        """Return the names of the themes the packaged files define."""
        return tuple(
            str(theme)
            for source in sorted(PACKAGED_THEMES.glob("*.yaml"))
            for theme in load_yaml_dict(source)
        )

    async def _async_reload_themes(self) -> str | None:
        """Ask the frontend to re-read the themes and return the error, if any."""
        try:
            await self._hass.services.async_call(
                FRONTEND_DOMAIN, RELOAD_THEMES_SERVICE, blocking=True
            )
        except HomeAssistantError as error:
            LOGGER.warning("%s", error)
            return str(error)
        return None

    def _update_issues(
        self, installed: tuple[str, ...], reload_error: str | None
    ) -> None:
        """Raise the repair issue that explains why the themes are not loaded."""
        if reload_error is not None:
            self._delete_issue(ISSUE_THEMES_NOT_LOADED)
            self._create_issue(ISSUE_THEMES_RELOAD_FAILED, {"error": reload_error})
            return
        self._delete_issue(ISSUE_THEMES_RELOAD_FAILED)
        if set(installed) <= self.loaded_themes:
            self._delete_issue(ISSUE_THEMES_NOT_LOADED)
            return
        self._create_issue(
            ISSUE_THEMES_NOT_LOADED,
            {
                "directory": f"{THEMES_DIRECTORY}/{DOMAIN}",
                "configuration": (
                    "frontend:\n  themes: !include_dir_merge_named themes"
                ),
            },
        )

    def _create_issue(self, issue_id: str, placeholders: dict[str, str]) -> None:
        """Create or update one of the integration's repair issues."""
        issue_registry.async_create_issue(
            self._hass,
            DOMAIN,
            issue_id,
            is_fixable=False,
            severity=issue_registry.IssueSeverity.WARNING,
            translation_key=issue_id,
            translation_placeholders=placeholders,
        )

    def _delete_issue(self, issue_id: str) -> None:
        """Remove one of the integration's repair issues, if present."""
        issue_registry.async_delete_issue(self._hass, DOMAIN, issue_id)
