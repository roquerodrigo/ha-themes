"""Runtime data stored on entry.runtime_data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..frontend_module import HaThemesFrontendModule
    from ..theme_installer import HaThemesThemeInstaller


@dataclass
class HaThemesData:
    """Data stored on entry.runtime_data for HA Themes."""

    theme_installer: HaThemesThemeInstaller
    frontend_module: HaThemesFrontendModule
    installed_themes: tuple[str, ...]
