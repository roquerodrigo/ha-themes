from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from atomicwrites import AtomicWriter
from homeassistant.components.frontend import DATA_THEMES
from homeassistant.const import EVENT_THEMES_UPDATED
from homeassistant.helpers import issue_registry
from homeassistant.util.file import WriteError
from pytest_homeassistant.common import async_capture_events

from custom_components.ha_themes.const import (
    DOMAIN,
    ISSUE_THEMES_NOT_LOADED,
    ISSUE_THEMES_RELOAD_FAILED,
)
from custom_components.ha_themes.theme_installer import HaThemesThemeInstaller

if TYPE_CHECKING:
    from pathlib import Path

    from homeassistant.core import HomeAssistant

THEMES_INCLUDE = "frontend:\n  themes: !include_dir_merge_named themes\n"


def issue(
    hass: HomeAssistant, issue_id: str = ISSUE_THEMES_NOT_LOADED
) -> issue_registry.IssueEntry | None:
    return issue_registry.async_get(hass).async_get_issue(DOMAIN, issue_id)


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
    hass: HomeAssistant,
    frontend: None,
    config_directory: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    installer = HaThemesThemeInstaller(hass)
    await installer.async_install()
    target = installer.target_directory
    kept = next(target.glob("*.yaml"))
    modified_at = kept.stat().st_mtime_ns
    stale = target / "retired-theme.yaml"
    stale.write_text("Retired: {}\n")
    theme_reloads = async_capture_events(hass, EVENT_THEMES_UPDATED)

    await installer.async_install()

    await hass.async_block_till_done()
    assert not stale.exists()
    assert len(theme_reloads) == 1
    assert kept.stat().st_mtime_ns == modified_at
    assert f"Removed {stale}" in caplog.text


async def test_unchanged_files_with_loaded_themes_skip_the_reload(
    hass: HomeAssistant, frontend: None, config_directory: Path
) -> None:
    installer = HaThemesThemeInstaller(hass)
    await installer.async_install()
    theme_reloads = async_capture_events(hass, EVENT_THEMES_UPDATED)

    installed = await installer.async_install()

    await hass.async_block_till_done()
    assert theme_reloads == []
    assert set(installed) <= installer.loaded_themes
    assert issue(hass) is None


async def test_unchanged_files_missing_from_the_frontend_are_reloaded(
    hass: HomeAssistant, frontend: None, config_directory: Path
) -> None:
    installer = HaThemesThemeInstaller(hass)
    installed = await installer.async_install()
    hass.data[DATA_THEMES].pop(installed[0])
    theme_reloads = async_capture_events(hass, EVENT_THEMES_UPDATED)

    await installer.async_install()

    await hass.async_block_till_done()
    assert len(theme_reloads) == 1
    assert installed[0] in installer.loaded_themes


async def test_uninstall_logs_files_it_cannot_remove(
    hass: HomeAssistant,
    frontend: None,
    config_directory: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    installer = HaThemesThemeInstaller(hass)
    await installer.async_install()
    failure = PermissionError("read-only")

    with patch("os.unlink", side_effect=failure):
        await installer.async_uninstall()

    assert "Could not remove" in caplog.text
    assert "read-only" in caplog.text


async def test_uninstall_without_installed_files_is_a_no_op(
    hass: HomeAssistant, frontend: None, config_directory: Path
) -> None:
    installer = HaThemesThemeInstaller(hass)

    await installer.async_uninstall()

    assert not installer.target_directory.exists()


async def test_outdated_files_are_rewritten(
    hass: HomeAssistant, frontend: None, config_directory: Path
) -> None:
    installer = HaThemesThemeInstaller(hass)
    await installer.async_install()
    installed = next(installer.target_directory.glob("*.yaml"))
    original = installed.read_text()
    installed.write_text("Outdated: {}\n")
    theme_reloads = async_capture_events(hass, EVENT_THEMES_UPDATED)

    await installer.async_install()

    await hass.async_block_till_done()
    assert installed.read_text() == original
    assert len(theme_reloads) == 1


async def test_interrupted_write_keeps_the_previous_file(
    hass: HomeAssistant, frontend: None, config_directory: Path
) -> None:
    installer = HaThemesThemeInstaller(hass)
    await installer.async_install()
    installed = next(installer.target_directory.glob("*.yaml"))
    installed.write_text("Outdated: {}\n")
    files_before = sorted(installer.target_directory.iterdir())

    with (
        patch.object(AtomicWriter, "commit", side_effect=OSError("disk full")),
        pytest.raises(WriteError),
    ):
        await installer.async_install()

    assert installed.read_text() == "Outdated: {}\n"
    assert sorted(installer.target_directory.iterdir()) == files_before


async def test_reload_failure_reports_the_error_instead_of_the_include(
    hass: HomeAssistant,
    frontend: None,
    config_directory: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    (config_directory / "configuration.yaml").write_text(THEMES_INCLUDE)
    (config_directory / "themes").mkdir()
    (config_directory / "themes" / "mine.yaml").write_text("Mine: 12\n")
    installer = HaThemesThemeInstaller(hass)

    await installer.async_install()

    assert issue(hass) is None
    failure = issue(hass, ISSUE_THEMES_RELOAD_FAILED)
    assert failure is not None
    assert failure.translation_placeholders is not None
    error = failure.translation_placeholders["error"]
    assert error.startswith("Failed to reload themes: ")
    assert "Failed to reload themes: Failed to reload themes" not in caplog.text
    assert error in caplog.text

    (config_directory / "themes" / "mine.yaml").unlink()
    await installer.async_install()
    assert issue(hass, ISSUE_THEMES_RELOAD_FAILED) is None
    assert issue(hass) is None


async def test_uninstall_removes_the_reload_failure_issue(
    hass: HomeAssistant, frontend: None, config_directory: Path
) -> None:
    (config_directory / "configuration.yaml").write_text(
        "frontend:\n  themes:\n    Broken: 12\n"
    )
    installer = HaThemesThemeInstaller(hass)
    await installer.async_install()
    assert issue(hass, ISSUE_THEMES_RELOAD_FAILED) is not None

    await installer.async_uninstall()

    assert issue(hass, ISSUE_THEMES_RELOAD_FAILED) is None


async def test_loaded_themes_is_empty_without_the_frontend(hass: HomeAssistant) -> None:
    assert HaThemesThemeInstaller(hass).loaded_themes == frozenset()
