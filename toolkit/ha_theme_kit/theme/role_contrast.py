"""Contrast of the role pairs, measured on the tokens the theme finally paints.

A role writes several tokens, raw `tokens` are applied after the roles, and backdrop blur gives
the card and dialog surfaces alpha, so a role value alone can differ from what the browser draws.
Each pair is measured over every combination of the two roles' tokens, with the backdrop
composited over what it sits on (the page over nothing, the surface over the page, everything
else over the surface), and the worst combination is reported.
"""

from itertools import product

from ha_theme_kit.color.css_color import contrast_on
from ha_theme_kit.theme.contrast_result import ContrastResult
from ha_theme_kit.theme.mode_colors import PAGE_ROLE, SURFACE_ROLE, ModeColors
from ha_theme_kit.theme.roles import CONTRAST_PAIRS, ROLE_TOKENS


def measure_role_pairs(colors: ModeColors) -> list[ContrastResult]:
    return [
        _worst_token_pair(colors, foreground, background, minimum)
        for foreground, background, minimum in CONTRAST_PAIRS
    ]


def _worst_token_pair(
    colors: ModeColors, foreground_role: str, background_role: str, minimum: float
) -> ContrastResult:
    results = [
        ContrastResult(
            colors.mode,
            foreground_role,
            background_role,
            contrast_on(
                colors.token(foreground_token),
                colors.opaque_token(background_token, _backdrop_of(background_role)),
            ),
            minimum,
            foreground_token,
            background_token,
        )
        for foreground_token, background_token in product(
            ROLE_TOKENS[foreground_role], ROLE_TOKENS[background_role]
        )
    ]
    unevaluable = [result for result in results if result.ratio is None]
    if unevaluable:
        return unevaluable[0]
    return min(results, key=lambda result: result.ratio or 0)


def _backdrop_of(role: str) -> str | None:
    if role == PAGE_ROLE:
        return None
    return PAGE_ROLE if role == SURFACE_ROLE else SURFACE_ROLE
