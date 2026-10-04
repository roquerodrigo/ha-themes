"""Scrollbar thumbs and slider tracks that stay at least as visible as the frontend's own.

The frontend draws `scrollbar-thumb-color` as the scrollbar thumb and, through
`slider-track-color`, as the unfilled track of round sliders (thermostat and light dials), on
the page and on cards and dialogs. A graphical part needs 3:1 against what it sits on, or, where
the frontend's own pair already falls short of 3:1 (its pale light-mode thumb), at least the
frontend's ratio.
"""

from dataclasses import dataclass

from ha_theme_kit.color.css_color import contrast_on
from ha_theme_kit.color.oklch import contrast_ratio
from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.mode_colors import ModeColors
from ha_theme_kit.theme.token_colors import resolve_token_color

TRACK_ROLE = "scrollbar"
TRACK_TOKEN = "scrollbar-thumb-color"
NON_TEXT_CONTRAST_FLOOR = 3.0
BACKDROP_TOKENS = {"background": "primary-background-color", "surface": "card-background-color"}
"""Each role the track is drawn on, and the token that paints it in stock HA, where cards fall
back from the unset `ha-card-background` to `card-background-color`."""


@dataclass(frozen=True)
class TrackPair:
    mode: str
    backdrop_role: str
    ratio: float | None
    minimum: float

    @property
    def passes(self) -> bool:
        return self.ratio is not None and self.ratio >= self.minimum


def measure_track_pairs(colors: ModeColors) -> list[TrackPair]:
    return [
        TrackPair(
            colors.mode,
            backdrop_role,
            contrast_on(colors.role(TRACK_ROLE), colors.opaque_role(backdrop_role)),
            contrast_floor(backdrop_token, colors.catalog, colors.mode),
        )
        for backdrop_role, backdrop_token in BACKDROP_TOKENS.items()
    ]


def contrast_floor(backdrop_token: str, catalog: TokenCatalog, mode: str) -> float:
    """3:1, lowered to the frontend's own ratio where the frontend falls short of it."""
    frontend_track = resolve_token_color(TRACK_TOKEN, {}, catalog, mode)
    frontend_backdrop = resolve_token_color(backdrop_token, {}, catalog, mode)
    if frontend_track is None or frontend_backdrop is None:
        return NON_TEXT_CONTRAST_FLOOR
    return min(NON_TEXT_CONTRAST_FLOOR, round(contrast_ratio(frontend_track, frontend_backdrop), 2))
