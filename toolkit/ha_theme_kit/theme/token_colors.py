import re

from ha_theme_kit.color.oklch import hex_to_rgb, rgb_to_hex
from ha_theme_kit.inventory.catalog import TokenCatalog

VARIABLE_REFERENCE = re.compile(r"var\(--(?P<name>[\w-]+)\)")
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
SHORT_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{3}$")


def resolve_token_color(
    key: str, tokens: dict[str, str], catalog: TokenCatalog, mode: str
) -> str | None:
    """Follow plain `var()` references through the theme, then the frontend's `mode` defaults."""
    seen: set[str] = set()
    while key not in seen:
        seen.add(key)
        value = tokens.get(key)
        if value is None:
            entry = catalog.find(key)
            value = entry and ((mode == "dark" and entry.dark) or entry.light)
        if value is None:
            return None
        if HEX_COLOR.match(value):
            return value
        if SHORT_HEX_COLOR.match(value):
            return rgb_to_hex(*hex_to_rgb(value))
        reference = VARIABLE_REFERENCE.fullmatch(value.strip())
        if reference is None:
            return None
        key = reference.group("name")
    return None
