"""Contrast of the semantic color layer, pair by pair as the frontend draws it.

The frontend paints its semantic tokens at fixed steps of the palette families: each
`ha-color-on-*` on the `ha-color-fill-*` of the same status and emphasis (the normal and quiet
ones also as plain text on the page and the surface), each `ha-color-border-*` on the page and
the surface, and each `ha-color-text-*` on the page and the surface. A theme palette moves what
those steps look like, so a pair can lose contrast the frontend had.

The rule: text reaches 4.5:1 and borders, as graphical parts, 3:1, or, where the frontend's own
pair already falls short, at least the frontend's ratio. Loud on-colors are held to 4.5:1
outright, since the builder moves the loud fills themselves (see `loud_fills`). Where a step
misses its floor, the builder moves the token along its family, away from its backdrops, to the
nearest step that meets every floor; the fills and surfaces keep their color. Disabled and
inverted colors are exempt, and so are tokens the frontend declares but never reads.
"""

import re
from collections import defaultdict
from dataclasses import dataclass
from functools import cache

from ha_theme_kit.color.css_color import contrast_on
from ha_theme_kit.color.oklch import contrast_ratio, relative_luminance
from ha_theme_kit.color.palette import PALETTE_STEPS
from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.contrast_result import ContrastResult
from ha_theme_kit.theme.mode_colors import PAGE_ROLE, SURFACE_ROLE, ModeColors
from ha_theme_kit.theme.token_colors import resolve_token_color

TEXT_CONTRAST_FLOOR = 4.5
NON_TEXT_CONTRAST_FLOOR = 3.0
FILL_STATES = ("resting", "hover", "active")
PAGE_TOKEN = "primary-background-color"
SURFACE_TOKEN = "ha-color-surface-default"
PAGE_AND_SURFACE = (PAGE_TOKEN, SURFACE_TOKEN)
ON_COLOR = re.compile(r"ha-color-on-(?P<status>[a-z]+)-(?P<tone>loud|normal|quiet)")
BORDER = re.compile(r"ha-color-border-[a-z]+-(?:loud|normal|quiet)")
TEXT = re.compile(r"ha-color-text-[a-z-]+|ha-color-on-surface-default")
EXEMPT = re.compile(r"-(?:disabled|inverted)\b")
PALETTE_REFERENCE = re.compile(r"var\(--ha-color-(?P<family>[a-z]+)-(?P<step>\d{2})\)")


@dataclass(frozen=True)
class SemanticPair:
    foreground: str
    backdrop: str
    minimum: float
    follows_frontend: bool
    """Whether the floor drops to the frontend's own ratio where that is lower than `minimum`."""

    def floor(self, catalog: TokenCatalog, mode: str) -> float:
        if not self.follows_frontend:
            return self.minimum
        return frontend_floor(self.foreground, self.backdrop, self.minimum, catalog, mode)


def semantic_pairs(catalog: TokenCatalog) -> list[SemanticPair]:
    pairs: list[SemanticPair] = []
    for key in sorted(_drawn_semantic_tokens(catalog)):
        if on_color := ON_COLOR.fullmatch(key):
            status, tone = on_color["status"], on_color["tone"]
            fills = [
                fill
                for state in FILL_STATES
                if catalog.find(fill := f"ha-color-fill-{status}-{tone}-{state}") is not None
            ]
            loud = tone == "loud"
            backdrops = fills if loud else [*fills, *PAGE_AND_SURFACE]
            pairs.extend(
                SemanticPair(key, backdrop, TEXT_CONTRAST_FLOOR, follows_frontend=not loud)
                for backdrop in backdrops
            )
        elif BORDER.fullmatch(key) or TEXT.fullmatch(key):
            minimum = NON_TEXT_CONTRAST_FLOOR if BORDER.fullmatch(key) else TEXT_CONTRAST_FLOOR
            pairs.extend(
                SemanticPair(key, backdrop, minimum, follows_frontend=True)
                for backdrop in PAGE_AND_SURFACE
            )
    return pairs


def _drawn_semantic_tokens(catalog: TokenCatalog) -> set[str]:
    return {
        entry.theme_key
        for entry in catalog.tokens.values()
        if entry.consumers > 0
        and (entry.light or entry.dark)
        and not EXEMPT.search(entry.theme_key)
        and any(pattern.fullmatch(entry.theme_key) for pattern in (ON_COLOR, BORDER, TEXT))
    }


def measure_semantic_pairs(colors: ModeColors) -> list[ContrastResult]:
    """Every semantic pair as the theme resolves it.

    Translucent fills and the surface are composited over the surface and the page they sit on.
    """
    return [
        ContrastResult(
            colors.mode,
            pair.foreground,
            pair.backdrop,
            contrast_on(
                colors.token(pair.foreground),
                colors.opaque_token(pair.backdrop, _backdrop_role(pair.backdrop)),
            ),
            pair.floor(colors.catalog, colors.mode),
        )
        for pair in semantic_pairs(colors.catalog)
    ]


def _backdrop_role(backdrop: str) -> str | None:
    """The page has nothing under it, the surface lies on the page and the fills on the surface."""
    return {PAGE_TOKEN: None, SURFACE_TOKEN: PAGE_ROLE}.get(backdrop, SURFACE_ROLE)


def frontend_floor(
    foreground: str, backdrop: str, minimum: float, catalog: TokenCatalog, mode: str
) -> float:
    """`minimum`, lowered to the frontend's own ratio where the frontend falls short of it."""
    frontend_foreground = resolve_token_color(foreground, {}, catalog, mode)
    frontend_backdrop = resolve_token_color(backdrop, {}, catalog, mode)
    if frontend_foreground is None or frontend_backdrop is None:
        return minimum
    return min(minimum, rounded_ratio(frontend_foreground, frontend_backdrop))


def frontend_palette_step(key: str, catalog: TokenCatalog, mode: str) -> tuple[str, str] | None:
    """The family and step the frontend paints `key` with in `mode`, None for other values."""
    entry = catalog.find(key)
    reference = entry and PALETTE_REFERENCE.fullmatch(
        (mode == "dark" and entry.dark) or entry.light or ""
    )
    return (reference["family"], reference["step"]) if reference else None


def build_semantic_colors(
    mode: str, tokens: dict[str, str], scales: dict[str, dict[str, str]]
) -> dict[str, str]:
    """Steps only for the tokens whose frontend step falls below a floor.

    Tokens already in `tokens` (roles, upstream fixes, loud on-colors) are left as they are.
    """
    catalog = frontend_catalog()
    pairs_by_token: dict[str, list[SemanticPair]] = defaultdict(list)
    for pair in semantic_pairs(catalog):
        pairs_by_token[pair.foreground].append(pair)
    colors: dict[str, str] = {}
    for key, pairs in pairs_by_token.items():
        step = frontend_palette_step(key, catalog, mode)
        if key in tokens or step is None or step[0] not in scales:
            continue
        family, frontend_step = step
        backdrops = [
            (color, pair.floor(catalog, mode))
            for pair in pairs
            if (color := resolve_token_color(pair.backdrop, tokens, catalog, mode)) is not None
        ]
        readable = nearest_readable_step(scales[family], frontend_step, backdrops)
        if readable != scales[family][frontend_step]:
            colors[key] = readable
    return colors


def nearest_readable_step(
    scale: dict[str, str], step: str, backdrops: list[tuple[str, float]]
) -> str:
    """The nearest step from `step`, away from the backdrops, that meets every floor.

    `backdrops` pairs each backdrop color with its floor. Falls back to `step` when no step does.
    """
    direction = _away_from(scale[step], backdrops)
    index = PALETTE_STEPS.index(step)
    while 0 <= index < len(PALETTE_STEPS):
        color = scale[PALETTE_STEPS[index]]
        if all(rounded_ratio(color, backdrop) >= floor for backdrop, floor in backdrops):
            return color
        index += direction
    return scale[step]


def _away_from(color: str, backdrops: list[tuple[str, float]]) -> int:
    """Steps grow lighter, so a color darker than most of its backdrops moves to lower steps."""
    luminance = relative_luminance(color)
    lighter = sum(relative_luminance(backdrop) > luminance for backdrop, _ in backdrops)
    return -1 if lighter * 2 >= len(backdrops) else 1


def rounded_ratio(foreground: str, background: str) -> float:
    return round(contrast_ratio(foreground, background), 2)


@cache
def frontend_catalog() -> TokenCatalog:
    return TokenCatalog.load()
