"""Checks that restyled named colors which compete for meaning stay apart, per mode.

Each group holds neighbouring hues that the frontend uses for different states of the same
domain or the same screen: alarm triggered against climate heat against arming, weather
sunny against lightning, cover against clear night, climate cool against fan only, the
energy dashboard's non-fossil against battery. Capping chroma and narrowing lightness pulls
those neighbours together, so every pair inside a group must keep the separation the
frontend's own palette has.
"""

from dataclasses import dataclass, field
from itertools import combinations

from ha_theme_kit.color.vision import color_distance
from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.builder import BuiltTheme
from ha_theme_kit.theme.mode_colors import ModeColors

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
    unresolved: list[tuple[str, str]] = field(default_factory=list)
    """Mode and name of each named color the theme sets that does not resolve to a color."""

    @property
    def passes(self) -> bool:
        return not self.close_pairs and not self.unresolved


def check_entity_separation(theme: BuiltTheme, catalog: TokenCatalog) -> EntitySeparationReport:
    close_pairs = []
    unresolved = []
    for mode in theme.modes:
        colors = named_colors(ModeColors.of_theme(theme, mode, catalog))
        unresolved.extend((mode, name) for name, color in colors.items() if color is None)
        close_pairs.extend(
            EntitySeparationPair(mode, first, second, distance)
            for first, second in competing_pairs()
            if (first_color := colors.get(first)) is not None
            and (second_color := colors.get(second)) is not None
            and (distance := round(color_distance(first_color, second_color), 1)) < DISTANCE_FLOOR
        )
    return EntitySeparationReport(close_pairs, unresolved)


def competing_pairs() -> list[tuple[str, str]]:
    return list(
        dict.fromkeys(pair for group in COMPETING_GROUPS for pair in combinations(group, 2))
    )


def named_colors(colors: ModeColors) -> dict[str, str | None]:
    """The competing named colors the theme sets, as painted on the surface; None where one
    does not resolve."""
    names = sorted({name for group in COMPETING_GROUPS for name in group})
    painted = {
        name: colors.opaque_token(f"{name}-color")
        for name in names
        if f"{name}-color" in colors.tokens
    }
    return {name: None if color is None else color.to_hex() for name, color in painted.items()}
