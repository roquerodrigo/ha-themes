"""Dark-mode checks that form fields and neutral fills stand apart from what they sit on.

Fields must read as boxes on the surface, disabled fields must differ from both the surface
and enabled fields, and the quiet fills, hover fills and `ha-color-surface-low` must not sink
below the page or surface they are drawn on. In light mode the frontend draws fields and
hovers as darker tints by design, so only dark mode is held to these floors.
"""

from dataclasses import dataclass

from ha_theme_kit.color.oklch import contrast_ratio, hex_to_oklch
from ha_theme_kit.color.vision import color_distance
from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.builder import BuiltTheme
from ha_theme_kit.theme.neutral_layers import (
    FORM_BACKGROUND,
    FORM_BACKGROUND_DISABLED,
    FORM_BACKGROUND_HOVER,
    NORMAL_HOVER,
    QUIET_ACTIVE,
    QUIET_HOVER,
    QUIET_RESTING,
    SURFACE_LOW,
)
from ha_theme_kit.theme.token_colors import HEX_COLOR, resolve_token_color

CHECKED_MODE = "dark"
FORM_CONTRAST_FLOOR = 1.2
DISTANCE_FLOOR = 2.0
DISTINCT_PAIRS = (
    (FORM_BACKGROUND, "surface"),
    (FORM_BACKGROUND_DISABLED, "surface"),
    (FORM_BACKGROUND_DISABLED, FORM_BACKGROUND),
)
NOT_DARKER_THAN = {
    QUIET_RESTING: "background",
    QUIET_ACTIVE: "background",
    SURFACE_LOW: "background",
    QUIET_HOVER: "surface",
    NORMAL_HOVER: "surface",
    FORM_BACKGROUND_HOVER: "surface",
}
CHECKED_NAMES = sorted(
    {
        *NOT_DARKER_THAN,
        *NOT_DARKER_THAN.values(),
        *(name for pair in DISTINCT_PAIRS for name in pair),
    }
)


@dataclass(frozen=True)
class FormSeparationReport:
    mode: str
    colors: dict[str, str]
    form_contrast: float | None
    close_pairs: list[tuple[str, str, float]]
    darker_fills: list[tuple[str, str]]

    @property
    def passes(self) -> bool:
        return (
            (self.form_contrast is None or self.form_contrast >= FORM_CONTRAST_FLOOR)
            and not self.close_pairs
            and not self.darker_fills
        )


def check_form_separation(theme: BuiltTheme, catalog: TokenCatalog) -> FormSeparationReport:
    tokens = theme.base | theme.modes[CHECKED_MODE]
    roles = theme.roles[CHECKED_MODE]
    colors = {
        name: color
        for name in CHECKED_NAMES
        if (color := _color(name, roles, tokens, catalog)) is not None
    }
    form_contrast = (
        round(contrast_ratio(colors[FORM_BACKGROUND], colors["surface"]), 2)
        if FORM_BACKGROUND in colors and "surface" in colors
        else None
    )
    close_pairs = [
        (first, second, distance)
        for first, second in DISTINCT_PAIRS
        if first in colors
        and second in colors
        and (distance := round(color_distance(colors[first], colors[second]), 2)) < DISTANCE_FLOOR
    ]
    darker_fills = [
        (token, base)
        for token, base in NOT_DARKER_THAN.items()
        if token in colors
        and base in colors
        and hex_to_oklch(colors[token]).lightness < hex_to_oklch(colors[base]).lightness
    ]
    return FormSeparationReport(CHECKED_MODE, colors, form_contrast, close_pairs, darker_fills)


def _color(
    name: str, roles: dict[str, str], tokens: dict[str, str], catalog: TokenCatalog
) -> str | None:
    if name in roles:
        return roles[name] if HEX_COLOR.match(roles[name]) else None
    return resolve_token_color(name, tokens, catalog)
