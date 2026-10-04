"""Normal and quiet on-colors that stay at least as readable as the frontend's own.

The frontend draws the normal and quiet text of each status (filled and plain buttons, badges,
alerts) at fixed steps of the palette families, on tinted fills of the same family and on the
page and surface. A theme palette moves what those steps look like, so the text can lose
contrast the frontend had (a pale brand orange in light mode, a lighter dark page).

The rule: on every fill state, the page and the surface, each on-color reaches 4.5:1, or, where
the frontend's own pair already falls short of 4.5:1, at least the frontend's ratio. Where the
frontend's step misses that floor, the builder moves the on-color along its family, away from
the fills, until it reaches it; the fills keep their tint. Disabled text is exempt.
"""

import re
from dataclasses import dataclass
from functools import cache

from ha_theme_kit.color.oklch import contrast_ratio, relative_luminance
from ha_theme_kit.color.palette import PALETTE_STEPS
from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.loud_fills import ON_COLOR_CONTRAST_FLOOR
from ha_theme_kit.theme.token_colors import resolve_token_color

TINTED_STATUSES = ("primary", "danger", "warning", "success", "neutral")
TINTED_TONES = ("normal", "quiet")
FILL_STATES = ("resting", "hover", "active")
PAGE_AND_SURFACE = ("primary-background-color", "ha-color-surface-default")
PALETTE_REFERENCE = re.compile(r"var\(--ha-color-(?P<family>[a-z]+)-(?P<step>\d{2})\)")


@dataclass(frozen=True)
class TintedPair:
    mode: str
    on_color_token: str
    backdrop_token: str
    ratio: float
    minimum: float

    @property
    def passes(self) -> bool:
        return self.ratio >= self.minimum


def on_color_token(status: str, tone: str) -> str:
    return f"ha-color-on-{status}-{tone}"


def backdrop_tokens(status: str, tone: str) -> tuple[str, ...]:
    fills = tuple(f"ha-color-fill-{status}-{tone}-{state}" for state in FILL_STATES)
    return (*fills, *PAGE_AND_SURFACE)


def measure_tinted_pairs(
    mode: str, tokens: dict[str, str], catalog: TokenCatalog
) -> list[TintedPair]:
    """Every normal and quiet on-color on its backdrops, as the theme resolves them in `mode`."""
    pairs = []
    for status in TINTED_STATUSES:
        for tone in TINTED_TONES:
            key = on_color_token(status, tone)
            on_color = resolve_token_color(key, tokens, catalog, mode)
            if on_color is None:
                continue
            for backdrop in backdrop_tokens(status, tone):
                color = resolve_token_color(backdrop, tokens, catalog, mode)
                if color is not None:
                    pairs.append(
                        TintedPair(
                            mode,
                            key,
                            backdrop,
                            _ratio(on_color, color),
                            contrast_floor(key, backdrop, catalog, mode),
                        )
                    )
    return pairs


def contrast_floor(on_color: str, backdrop: str, catalog: TokenCatalog, mode: str) -> float:
    """4.5:1, lowered to the frontend's own ratio where the frontend falls short of it."""
    frontend_on_color = resolve_token_color(on_color, {}, catalog, mode)
    frontend_backdrop = resolve_token_color(backdrop, {}, catalog, mode)
    if frontend_on_color is None or frontend_backdrop is None:
        return ON_COLOR_CONTRAST_FLOOR
    return min(ON_COLOR_CONTRAST_FLOOR, _ratio(frontend_on_color, frontend_backdrop))


def build_tinted_on_colors(
    mode: str, tokens: dict[str, str], scales: dict[str, dict[str, str]]
) -> dict[str, str]:
    """On-colors only for the pairs whose frontend step falls below the floor."""
    catalog = _frontend_catalog()
    on_colors: dict[str, str] = {}
    for status in TINTED_STATUSES:
        for tone in TINTED_TONES:
            key = on_color_token(status, tone)
            entry = catalog.find(key)
            reference = entry and PALETTE_REFERENCE.fullmatch(
                (mode == "dark" and entry.dark) or entry.light or ""
            )
            if not reference or reference["family"] not in scales:
                continue
            backdrops = [
                (color, contrast_floor(key, backdrop, catalog, mode))
                for backdrop in backdrop_tokens(status, tone)
                if (color := resolve_token_color(backdrop, tokens, catalog, mode)) is not None
            ]
            readable = readable_on_color(scales[reference["family"]], reference["step"], backdrops)
            if readable != scales[reference["family"]][reference["step"]]:
                on_colors[key] = readable
    return on_colors


def readable_on_color(scale: dict[str, str], step: str, backdrops: list[tuple[str, float]]) -> str:
    """The nearest step from `step`, away from the backdrops, that meets every floor.

    `backdrops` pairs each backdrop color with its floor. Falls back to `step` when no step does.
    """
    start = PALETTE_STEPS.index(step)
    direction = _away_from(scale[step], backdrops)
    index = start
    while 0 <= index < len(PALETTE_STEPS):
        color = scale[PALETTE_STEPS[index]]
        if all(_ratio(color, backdrop) >= floor for backdrop, floor in backdrops):
            return color
        index += direction
    return scale[step]


def _away_from(on_color: str, backdrops: list[tuple[str, float]]) -> int:
    """Steps grow lighter, so text darker than most of its backdrops moves to lower steps."""
    on_luminance = relative_luminance(on_color)
    darker = sum(relative_luminance(backdrop) > on_luminance for backdrop, _ in backdrops)
    return -1 if darker * 2 >= len(backdrops) else 1


def _ratio(foreground: str, background: str) -> float:
    return round(contrast_ratio(foreground, background), 2)


@cache
def _frontend_catalog() -> TokenCatalog:
    return TokenCatalog.load()
