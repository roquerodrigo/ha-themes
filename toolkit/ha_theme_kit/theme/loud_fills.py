"""Loud danger, warning, success and neutral fills whose on-color stays readable.

The frontend draws white text on these fills at fixed steps of the palette families. A theme
palette moves what those steps look like, so white can fall below 4.5:1 (a pale brand orange in
light mode, a mid grey in dark mode). For each fill the builder keeps the frontend's steps and
white where white reads, takes the darkest neutral as the on-color where that reads instead, and
otherwise moves the resting and hover steps together along the family, darker under white or
lighter under the dark on-color, until one of them does.
"""

from dataclasses import dataclass

from ha_theme_kit.color.oklch import contrast_ratio, relative_luminance
from ha_theme_kit.color.palette import PALETTE_STEPS

LOUD_FILL_STATUSES = ("danger", "warning", "success", "neutral")
LOUD_FILL_STATES = ("resting", "hover", "active")
ON_COLOR_CONTRAST_FLOOR = 4.5
WHITE = "#ffffff"
DARK_ON_COLOR_STEP = "05"

FRONTEND_LOUD_STEPS: dict[str, dict[str, tuple[str, str, str]]] = {
    "light": {
        "danger": ("red", "50", "40"),
        "warning": ("orange", "70", "50"),
        "success": ("green", "50", "40"),
        "neutral": ("neutral", "40", "30"),
    },
    "dark": {
        "danger": ("red", "40", "30"),
        "warning": ("orange", "40", "30"),
        "success": ("green", "40", "30"),
        "neutral": ("neutral", "60", "70"),
    },
}
"""Family, resting step and hover step of each loud fill; active repeats the resting step."""


@dataclass(frozen=True)
class LoudFill:
    resting_step: str
    hover_step: str
    resting: str
    hover: str
    on_color: str

    @property
    def readable(self) -> bool:
        return (
            min(
                contrast_ratio(self.on_color, self.resting),
                contrast_ratio(self.on_color, self.hover),
            )
            >= ON_COLOR_CONTRAST_FLOOR
        )


def fill_token(status: str, state: str) -> str:
    return f"ha-color-fill-{status}-loud-{state}"


def on_color_token(status: str) -> str:
    return f"ha-color-on-{status}-loud"


def build_loud_fills(mode: str, scales: dict[str, dict[str, str]]) -> dict[str, str]:
    """Tokens only for the fills whose frontend steps and white on-color do not read."""
    tokens: dict[str, str] = {}
    on_colors = (WHITE, scales["neutral"][DARK_ON_COLOR_STEP])
    for status, (family, resting_step, hover_step) in FRONTEND_LOUD_STEPS[mode].items():
        fill = readable_loud_fill(scales[family], resting_step, hover_step, on_colors)
        if fill.on_color == WHITE and fill.resting_step == resting_step:
            continue
        tokens[on_color_token(status)] = fill.on_color
        tokens[fill_token(status, "resting")] = fill.resting
        tokens[fill_token(status, "active")] = fill.resting
        tokens[fill_token(status, "hover")] = fill.hover
    return tokens


def readable_loud_fill(
    scale: dict[str, str], resting_step: str, hover_step: str, on_colors: tuple[str, ...]
) -> LoudFill:
    """The smallest move along the scale that makes one on-color readable, in `on_colors` order."""
    resting_index, hover_index = PALETTE_STEPS.index(resting_step), PALETTE_STEPS.index(hover_step)
    fallback = _fill(scale, resting_index, hover_index, on_colors[0])
    for distance in range(len(PALETTE_STEPS)):
        for on_color in on_colors:
            offset = distance * _lightening_direction(on_color, scale[resting_step])
            shifted_resting, shifted_hover = resting_index + offset, hover_index + offset
            if not all(
                0 <= index < len(PALETTE_STEPS) for index in (shifted_resting, shifted_hover)
            ):
                continue
            fill = _fill(scale, shifted_resting, shifted_hover, on_color)
            if fill.readable:
                return fill
    return fallback


def _lightening_direction(on_color: str, fill: str) -> int:
    """Steps grow lighter, so a light on-color needs darker steps and a dark one lighter steps."""
    return -1 if relative_luminance(on_color) > relative_luminance(fill) else 1


def _fill(scale: dict[str, str], resting_index: int, hover_index: int, on_color: str) -> LoudFill:
    resting_step, hover_step = PALETTE_STEPS[resting_index], PALETTE_STEPS[hover_index]
    return LoudFill(resting_step, hover_step, scale[resting_step], scale[hover_step], on_color)
