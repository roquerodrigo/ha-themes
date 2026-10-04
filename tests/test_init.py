from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL, DATA_THEMES
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import issue_registry

from custom_components.ha_themes.const import (
    DOMAIN,
    ISSUE_THEMES_NOT_LOADED,
    ISSUE_THEMES_RELOAD_FAILED,
)
from custom_components.ha_themes.theme_installer import PACKAGED_THEMES

if TYPE_CHECKING:
    from pathlib import Path

    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry


THEMES_INCLUDE = "frontend:\n  themes: !include_dir_merge_named themes\n"


def packaged_theme_files() -> set[str]:
    return {path.name for path in PACKAGED_THEMES.glob("*.yaml")}


def issue(
    hass: HomeAssistant, issue_id: str = ISSUE_THEMES_NOT_LOADED
) -> issue_registry.IssueEntry | None:
    return issue_registry.async_get(hass).async_get_issue(DOMAIN, issue_id)


async def reload_themes(hass: HomeAssistant) -> None:
    await hass.services.async_call("frontend", "reload_themes", blocking=True)
    await hass.async_block_till_done()


async def test_setup_installs_and_loads_the_themes(
    hass: HomeAssistant, setup_integration: MockConfigEntry, config_directory: Path
) -> None:
    installed = config_directory / "themes" / DOMAIN
    assert {path.name for path in installed.glob("*.yaml")} == packaged_theme_files()
    runtime = setup_integration.runtime_data
    assert runtime.installed_themes
    assert set(runtime.installed_themes) <= set(hass.data[DATA_THEMES])
    assert (
        issue_registry.async_get(hass).async_get_issue(DOMAIN, ISSUE_THEMES_NOT_LOADED)
        is None
    )


async def test_setup_registers_the_module_under_a_content_hash(
    hass: HomeAssistant, setup_integration: MockConfigEntry
) -> None:
    url = setup_integration.runtime_data.frontend_module.url
    assert url is not None
    assert url.startswith(f"/{DOMAIN}/ha-themes.js?v=")
    assert url in hass.data[DATA_EXTRA_MODULE_URL].urls


async def test_unload_stops_loading_the_module_and_keeps_the_themes(
    hass: HomeAssistant, setup_integration: MockConfigEntry, config_directory: Path
) -> None:
    url = setup_integration.runtime_data.frontend_module.url
    assert await hass.config_entries.async_unload(setup_integration.entry_id)
    assert setup_integration.state is ConfigEntryState.NOT_LOADED
    assert url not in hass.data[DATA_EXTRA_MODULE_URL].urls
    assert any((config_directory / "themes" / DOMAIN).glob("*.yaml"))


async def test_reload_registers_the_module_again(
    hass: HomeAssistant, setup_integration: MockConfigEntry
) -> None:
    assert await hass.config_entries.async_reload(setup_integration.entry_id)
    await hass.async_block_till_done()
    assert setup_integration.state is ConfigEntryState.LOADED
    url = setup_integration.runtime_data.frontend_module.url
    assert url in hass.data[DATA_EXTRA_MODULE_URL].urls


async def test_removal_deletes_the_installed_themes(
    hass: HomeAssistant, setup_integration: MockConfigEntry, config_directory: Path
) -> None:
    installed_names = setup_integration.runtime_data.installed_themes
    assert await hass.config_entries.async_remove(setup_integration.entry_id)
    await hass.async_block_till_done()
    assert not (config_directory / "themes" / DOMAIN).exists()
    assert not set(installed_names) & set(hass.data[DATA_THEMES])


async def test_theme_reload_clears_the_issue_once_the_include_is_added(
    hass: HomeAssistant, setup_integration: MockConfigEntry, config_directory: Path
) -> None:
    (config_directory / "configuration.yaml").write_text("homeassistant:\n")
    await reload_themes(hass)
    assert issue(hass) is not None

    (config_directory / "configuration.yaml").write_text(THEMES_INCLUDE)
    await reload_themes(hass)
    assert issue(hass) is None


async def test_theme_reload_clears_a_previous_reload_failure(
    hass: HomeAssistant, setup_integration: MockConfigEntry, config_directory: Path
) -> None:
    (config_directory / "configuration.yaml").write_text(
        "frontend:\n  themes:\n    Broken: 12\n"
    )
    assert await hass.config_entries.async_reload(setup_integration.entry_id)
    await hass.async_block_till_done()
    assert issue(hass, ISSUE_THEMES_RELOAD_FAILED) is not None

    (config_directory / "configuration.yaml").write_text(THEMES_INCLUDE)
    await reload_themes(hass)
    assert issue(hass, ISSUE_THEMES_RELOAD_FAILED) is None
    assert issue(hass) is None


async def test_unload_removes_the_issue_and_stops_watching_reloads(
    hass: HomeAssistant, setup_integration: MockConfigEntry, config_directory: Path
) -> None:
    (config_directory / "configuration.yaml").write_text("homeassistant:\n")
    await reload_themes(hass)
    assert issue(hass) is not None

    assert await hass.config_entries.async_unload(setup_integration.entry_id)
    assert issue(hass) is None

    await reload_themes(hass)
    assert issue(hass) is None
