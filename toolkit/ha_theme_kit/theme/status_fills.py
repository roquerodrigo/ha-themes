"""Dark-mode checks for the danger, warning and success fills.

The frontend paints those fills from steps 05-20 of the red, orange and green families. A
tonal scale generated from a seed drifts towards black and towards red there, so warning
reads as danger and quiet fills look like holes in the page. In light mode the quiet fills
are near-white tints by design (the frontend's own sit about ΔE 1.5 apart), so only dark
mode is held to these floors.
"""

import re
from dataclasses import dataclass
from itertools import combinations

from ha_theme_kit.color.oklch import hex_to_oklch
from ha_theme_kit.color.vision import color_distance
from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.builder import BuiltTheme

STATUSES = ("danger", "warning", "success")
FILL_TONES = ("quiet", "normal")
CHECKED_MODE = "dark"
DISTANCE_FLOOR = 5.0
VARIABLE_REFERENCE = re.compile(r"var\(--(?P<name>[\w-]+)\)")
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


@dataclass(frozen=True)
class StatusFillPair:
    tone: str
    first: str
    second: str
    distance: float


@dataclass(frozen=True)
class StatusFillReport:
    mode: str
    background: str
    fills: dict[str, str]
    darker_than_background: list[str]
    close_pairs: list[StatusFillPair]

    @property
    def passes(self) -> bool:
        return not self.darker_than_background and not self.close_pairs


def fill_token(status: str, tone: str) -> str:
    return f"ha-color-fill-{status}-{tone}-resting"


def check_status_fills(theme: BuiltTheme, catalog: TokenCatalog) -> StatusFillReport:
    tokens = theme.base | theme.modes[CHECKED_MODE]
    background = theme.roles[CHECKED_MODE]["background"]
    fills = {
        fill_token(status, tone): color
        for tone in FILL_TONES
        for status in STATUSES
        if (color := _resolve(fill_token(status, tone), tokens, catalog)) is not None
    }
    background_lightness = hex_to_oklch(background).lightness
    darker = [
        token
        for status in STATUSES
        if (token := fill_token(status, "quiet")) in fills
        and hex_to_oklch(fills[token]).lightness < background_lightness
    ]
    close_pairs = []
    for tone in FILL_TONES:
        for first, second in combinations(STATUSES, 2):
            first_color = fills.get(fill_token(first, tone))
            second_color = fills.get(fill_token(second, tone))
            if first_color is None or second_color is None:
                continue
            distance = round(color_distance(first_color, second_color), 2)
            if distance < DISTANCE_FLOOR:
                close_pairs.append(StatusFillPair(tone, first, second, distance))
    return StatusFillReport(CHECKED_MODE, background, fills, darker, close_pairs)


def _resolve(key: str, tokens: dict[str, str], catalog: TokenCatalog) -> str | None:
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
