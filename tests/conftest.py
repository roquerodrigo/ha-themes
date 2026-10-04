from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_themes.const import DOMAIN

if TYPE_CHECKING:
    from pathlib import Path

    from homeassistant.core import HomeAssistant

pytest_plugins = "pytest_homeassistant_custom_component"

THEMES_INCLUDE = "frontend:\n  themes: !include_dir_merge_named themes\n"


@pytest.fixture
def config_directory(hass: HomeAssistant, tmp_path: Path) -> Path:
    hass.config.config_dir = str(tmp_path)
    (tmp_path / "configuration.yaml").write_text(THEMES_INCLUDE)
    return tmp_path


@pytest.fixture
async def frontend(hass: HomeAssistant, config_directory: Path) -> None:
    assert await async_setup_component(hass, "frontend", {})
    await hass.async_block_till_done()


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant, frontend: None, enable_custom_integrations: None
) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, data={}, title="HA Themes")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
