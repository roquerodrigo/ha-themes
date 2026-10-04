"""Scrollbar thumbs and slider tracks that stay at least as visible as the frontend's own.

The frontend draws `scrollbar-thumb-color` as the scrollbar thumb and, through
`slider-track-color`, as the unfilled track of round sliders (thermostat and light dials), on
the page and on cards and dialogs. A graphical part needs 3:1 against what it sits on, or, where
the frontend's own pair already falls short of 3:1 (its pale light-mode thumb), at least the
frontend's ratio.
"""

from ha_theme_kit.color.css_color import contrast_on
from ha_theme_kit.theme.contrast_result import ContrastResult
from ha_theme_kit.theme.mode_colors import ModeColors
from ha_theme_kit.theme.semantic_layer import NON_TEXT_CONTRAST_FLOOR, frontend_floor

TRACK_ROLE = "scrollbar"
TRACK_TOKEN = "scrollbar-thumb-color"
BACKDROP_TOKENS = {"background": "primary-background-color", "surface": "card-background-color"}
"""Each role the track is drawn on, and the token that paints it in stock HA, where cards fall
back from the unset `ha-card-background` to `card-background-color`."""


def measure_track_pairs(colors: ModeColors) -> list[ContrastResult]:
    return [
        ContrastResult(
            colors.mode,
            TRACK_ROLE,
            backdrop_role,
            contrast_on(colors.role(TRACK_ROLE), colors.opaque_role(backdrop_role)),
            frontend_floor(
                TRACK_TOKEN, backdrop_token, NON_TEXT_CONTRAST_FLOOR, colors.catalog, colors.mode
            ),
        )
        for backdrop_role, backdrop_token in BACKDROP_TOKENS.items()
    ]
