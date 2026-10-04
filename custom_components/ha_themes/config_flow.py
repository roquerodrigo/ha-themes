"""Config flow for ha_themes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN

if TYPE_CHECKING:
    from collections.abc import Mapping


class HaThemesFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for HA Themes: a single confirmation, nothing to configure."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: Mapping[str, str] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Confirm installing the themes."""
        if user_input is not None:
            return self.async_create_entry(title="HA Themes", data={})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({}))
