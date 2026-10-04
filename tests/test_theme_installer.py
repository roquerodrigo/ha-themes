from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers import issue_registry

from custom_components.ha_themes.const import DOMAIN, ISSUE_THEMES_NOT_LOADED
from custom_components.ha_themes.theme_installer import HaThemesThemeInstaller

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from homeassistant.core import HomeAssistant

THEMES_INCLUDE = "frontend:\n  themes: !include_dir_merge_named themes\n"


def issue(hass: HomeAssistant) -> issue_registry.IssueEntry | None:
    return issue_registry.async_get(hass).async_get_issue(
        DOMAIN, ISSUE_THEMES_NOT_LOADED
    )


async def test_missing_themes_include_raises_a_repair_issue(
    hass: HomeAssistant, frontend: None, config_directory: Path
) -> None:
    (config_directory / "configuration.yaml").write_text("homeassistant:\n")
    installed = await HaThemesThemeInstaller(hass).async_install()
    assert installed
    repair = issue(hass)
    assert repair is not None
    assert repair.translation_placeholders == {
        "directory": f"themes/{DOMAIN}",
        "configuration": THEMES_INCLUDE.rstrip("\n"),
    }

    (config_directory / "configuration.yaml").write_text(THEMES_INCLUDE)
    await HaThemesThemeInstaller(hass).async_install()
    assert issue(hass) is None


async def test_stale_files_are_removed_and_unchanged_files_kept(
    hass: HomeAssistant, frontend: None, config_directory: Path
) -> None:
    installer = HaThemesThemeInstaller(hass)
    await installer.async_install()
    target = installer.target_directory
    stale = target / "retired-theme.yaml"
    stale.write_text("Retired: {}\n")
    kept = next(target.glob("*.yaml"))
    modified_at = kept.stat().st_mtime_ns

    await installer.async_install()

    assert not stale.exists()
    assert kept.stat().st_mtime_ns == modified_at


async def test_outdated_files_are_rewritten(
    hass: HomeAssistant, frontend: None, config_directory: Path
) -> None:
    installer = HaThemesThemeInstaller(hass)
    await installer.async_install()
    installed = next(installer.target_directory.glob("*.yaml"))
    original = installed.read_text()
    installed.write_text("Outdated: {}\n")

    await installer.async_install()

    assert installed.read_text() == original


async def test_reload_failure_is_logged_and_reported(
    hass: HomeAssistant,
    frontend: None,
    config_directory: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    (config_directory / "configuration.yaml").write_text(
        "frontend:\n  themes:\n    Broken: 12\n"
    )
    await HaThemesThemeInstaller(hass).async_install()
    assert "Failed to reload themes" in caplog.text
    assert issue(hass) is not None


async def test_loaded_themes_is_empty_without_the_frontend(hass: HomeAssistant) -> None:
    assert HaThemesThemeInstaller(hass).loaded_themes == frozenset()
