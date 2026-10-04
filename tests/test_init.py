from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL, DATA_THEMES
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import issue_registry

from custom_components.ha_themes.const import DOMAIN, ISSUE_THEMES_NOT_LOADED
from custom_components.ha_themes.theme_installer import PACKAGED_THEMES

if TYPE_CHECKING:
    from pathlib import Path

    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry


def packaged_theme_files() -> set[str]:
    return {path.name for path in PACKAGED_THEMES.glob("*.yaml")}


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
