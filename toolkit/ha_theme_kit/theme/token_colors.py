import re

from ha_theme_kit.inventory.catalog import TokenCatalog

VARIABLE_REFERENCE = re.compile(r"var\(--(?P<name>[\w-]+)\)")
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def resolve_token_color(key: str, tokens: dict[str, str], catalog: TokenCatalog) -> str | None:
    """Follow plain `var()` references through the theme, then the frontend's dark defaults."""
    seen: set[str] = set()
    while key not in seen:
        seen.add(key)
        value = tokens.get(key)
        if value is None:
            entry = catalog.find(key)
            value = entry and (entry.dark or entry.light)
        if value is None:
            return None
        if HEX_COLOR.match(value):
            return value
        reference = VARIABLE_REFERENCE.fullmatch(value.strip())
        if reference is None:
            return None
        key = reference.group("name")
    return None
