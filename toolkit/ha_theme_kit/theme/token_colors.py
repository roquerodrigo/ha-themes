import re

from ha_theme_kit.color.css_color import CssColor, parse_css_color
from ha_theme_kit.inventory.catalog import TokenCatalog

VARIABLE_REFERENCE = re.compile(
    r"var\(\s*--(?P<name>[\w-]+)\s*(?:,\s*(?P<fallback>.*?))?\s*\)", re.DOTALL
)


def resolve_color_value(
    value: str, tokens: dict[str, str], catalog: TokenCatalog, mode: str
) -> CssColor | None:
    """Follow `var()` references, with their fallbacks, through the theme and then the
    frontend's `mode` defaults. None when the value never reaches a color this module parses."""
    seen: set[str] = set()
    text = value.strip()
    while reference := VARIABLE_REFERENCE.fullmatch(text):
        name, fallback = reference["name"], reference["fallback"]
        if name in seen:
            return None
        seen.add(name)
        declared = declared_value(name, tokens, catalog, mode)
        if declared is None and fallback is None:
            return None
        text = (fallback if declared is None else declared).strip()
    return parse_css_color(text)


def resolve_token_value(
    key: str, tokens: dict[str, str], catalog: TokenCatalog, mode: str
) -> CssColor | None:
    return resolve_color_value(f"var(--{key})", tokens, catalog, mode)


def resolve_token_color(
    key: str, tokens: dict[str, str], catalog: TokenCatalog, mode: str
) -> str | None:
    """The token's color as opaque hex, None when it is translucent or does not resolve."""
    color = resolve_token_value(key, tokens, catalog, mode)
    return color.to_hex() if color is not None and color.is_opaque else None


def declared_value(
    key: str, tokens: dict[str, str], catalog: TokenCatalog, mode: str
) -> str | None:
    if key in tokens:
        return tokens[key]
    entry = catalog.find(key)
    return entry and ((mode == "dark" and entry.dark) or entry.light)
