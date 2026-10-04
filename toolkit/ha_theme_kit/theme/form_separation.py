"""Dark-mode checks that form fields and neutral fills stand apart from what they sit on.

Filled fields must read as boxes on the surface, disabled fields must differ from both the
surface and enabled fields, and the quiet fills, hover fills and `ha-color-surface-low` must not
sink below the page or surface they are drawn on. In light mode the frontend draws fields and
hovers as darker tints by design, so only dark mode is held to these floors. A theme with
`field_outline` draws its fields as clear outlined boxes, so the field fill checks do not apply;
the form hover fill is still checked, since checkboxes paint it on hover.
"""

from dataclasses import dataclass, field

from ha_theme_kit.color.oklch import contrast_ratio, hex_to_oklch
from ha_theme_kit.color.vision import color_distance
from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.builder import BuiltTheme
from ha_theme_kit.theme.mode_colors import ModeColors
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
    unresolved: list[str] = field(default_factory=list)
    """Checked roles and tokens that do not resolve to a measurable color."""
    fields_filled: bool = True
    """False when the theme outlines its fields without a fill, which skips the field checks."""

    @property
    def passes(self) -> bool:
        return (
            (
                not self.fields_filled
                or (self.form_contrast is not None and self.form_contrast >= FORM_CONTRAST_FLOOR)
            )
            and not self.close_pairs
            and not self.darker_fills
            and not self.unresolved
        )


def check_form_separation(theme: BuiltTheme, catalog: TokenCatalog) -> FormSeparationReport:
    mode_colors = ModeColors.of_theme(theme, CHECKED_MODE, catalog)
    resolved = {
        name: mode_colors.opaque_role(name)
        if name in theme.roles[CHECKED_MODE]
        else mode_colors.opaque_token(name, NOT_DARKER_THAN.get(name, "surface"))
        for name in CHECKED_NAMES
    }
    colors = {name: color.to_hex() for name, color in resolved.items() if color is not None}
    unresolved = [name for name, color in resolved.items() if color is None]
    fields_filled = not theme.definition.field_outline
    form_contrast = (
        round(contrast_ratio(colors[FORM_BACKGROUND], colors["surface"]), 2)
        if fields_filled and FORM_BACKGROUND in colors and "surface" in colors
        else None
    )
    close_pairs = [
        (first, second, distance)
        for first, second in DISTINCT_PAIRS
        if fields_filled
        and first in colors
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
    return FormSeparationReport(
        CHECKED_MODE, colors, form_contrast, close_pairs, darker_fills, unresolved, fields_filled
    )
