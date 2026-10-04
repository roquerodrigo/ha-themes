from __future__ import annotations

from typing import TYPE_CHECKING

from custom_components.ha_themes.const import DOMAIN
from custom_components.ha_themes.diagnostics import async_get_config_entry_diagnostics

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_diagnostics_report_installed_and_loaded_themes(
    hass: HomeAssistant, setup_integration: MockConfigEntry
) -> None:
    diagnostics = await async_get_config_entry_diagnostics(hass, setup_integration)
    assert diagnostics["installed_themes"] == list(
        setup_integration.runtime_data.installed_themes
    )
    assert diagnostics["loaded_themes"] == sorted(diagnostics["installed_themes"])
    assert diagnostics["themes_directory"].endswith(f"themes/{DOMAIN}")
    assert diagnostics["frontend_module_url"].startswith(f"/{DOMAIN}/ha-themes.js?v=")
