"""Checks that restyled named colors which compete for meaning stay apart, per mode.

Each group holds neighbouring hues that the frontend uses for different states of the same
domain or the same screen: alarm triggered against climate heat against arming, weather
sunny against lightning, cover against clear night, climate cool against fan only, the
energy dashboard's non-fossil against battery. Capping chroma and narrowing lightness pulls
those neighbours together, so every pair inside a group must keep the separation the
frontend's own palette has.
"""

from dataclasses import dataclass
from itertools import combinations

from ha_theme_kit.color.vision import color_distance
from ha_theme_kit.theme.builder import BuiltTheme

COMPETING_GROUPS = (
    ("pink", "red", "deep-orange", "orange"),
    ("orange", "amber", "yellow", "lime"),
    ("purple", "deep-purple", "indigo"),
    ("indigo", "blue", "light-blue", "cyan"),
    ("teal", "green", "light-green"),
)
DISTANCE_FLOOR = 5.0
"""OKLab ΔE x100: the frontend's closest pair, blue and light-blue, sits 5.1 apart."""


@dataclass(frozen=True)
class EntitySeparationPair:
    mode: str
    first: str
    second: str
    distance: float


@dataclass(frozen=True)
class EntitySeparationReport:
    close_pairs: list[EntitySeparationPair]

    @property
    def passes(self) -> bool:
        return not self.close_pairs


def check_entity_separation(theme: BuiltTheme) -> EntitySeparationReport:
    close_pairs = []
    for mode, mode_tokens in theme.modes.items():
        colors = named_colors(theme.base | mode_tokens)
        close_pairs.extend(
            EntitySeparationPair(mode, first, second, distance)
            for first, second in competing_pairs()
            if first in colors
            and second in colors
            and (distance := round(color_distance(colors[first], colors[second]), 1))
            < DISTANCE_FLOOR
        )
    return EntitySeparationReport(close_pairs)


def competing_pairs() -> list[tuple[str, str]]:
    return list(
        dict.fromkeys(pair for group in COMPETING_GROUPS for pair in combinations(group, 2))
    )


def named_colors(tokens: dict[str, str]) -> dict[str, str]:
    names = {name for group in COMPETING_GROUPS for name in group}
    return {
        name: color
        for name in names
        if (color := tokens.get(f"{name}-color")) is not None and color.startswith("#")
    }
