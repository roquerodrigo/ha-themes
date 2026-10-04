from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.ha_themes.const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_user_step_creates_the_entry(
    hass: HomeAssistant, frontend: None, enable_custom_integrations: None
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "HA Themes"
    assert result["data"] == {}


async def test_only_one_entry_is_allowed(
    hass: HomeAssistant, setup_integration: MockConfigEntry
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"
