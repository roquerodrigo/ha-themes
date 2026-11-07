"""Custom types for ha_themes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .diagnostics_payload import HaThemesDiagnosticsPayload
from .runtime import HaThemesData

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry


type HaThemesConfigEntry = ConfigEntry[HaThemesData]

__all__ = [
    "HaThemesConfigEntry",
    "HaThemesData",
    "HaThemesDiagnosticsPayload",
]
