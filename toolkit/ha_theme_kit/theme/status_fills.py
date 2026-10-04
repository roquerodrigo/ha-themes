"""Dark-mode checks for the danger, warning and success fills.

The frontend paints those fills from steps 05-20 of the red, orange and green families. A
tonal scale generated from a seed drifts towards black and towards red there, so warning
reads as danger and quiet fills look like holes in the page. In light mode the quiet fills
are near-white tints by design (the frontend's own sit about ΔE 1.5 apart), so only dark
mode is held to these floors.
"""

from dataclasses import dataclass, field
from itertools import combinations

from ha_theme_kit.color.oklch import hex_to_oklch
from ha_theme_kit.color.vision import color_distance
from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.builder import BuiltTheme
from ha_theme_kit.theme.mode_colors import PAGE_ROLE, ModeColors

STATUSES = ("danger", "warning", "success")
FILL_TONES = ("quiet", "normal")
CHECKED_MODE = "dark"
DISTANCE_FLOOR = 5.0


@dataclass(frozen=True)
class StatusFillPair:
    tone: str
    first: str
    second: str
    distance: float


@dataclass(frozen=True)
class StatusFillReport:
    mode: str
    background: str | None
    fills: dict[str, str]
    darker_than_background: list[str]
    close_pairs: list[StatusFillPair]
    unresolved: list[str] = field(default_factory=list)
    """The background role and fill tokens that do not resolve to a measurable color."""

    @property
    def passes(self) -> bool:
        return not self.darker_than_background and not self.close_pairs and not self.unresolved


def fill_token(status: str, tone: str) -> str:
    return f"ha-color-fill-{status}-{tone}-resting"


def check_status_fills(theme: BuiltTheme, catalog: TokenCatalog) -> StatusFillReport:
    colors = ModeColors.of_theme(theme, CHECKED_MODE, catalog)
    page = colors.opaque_role(PAGE_ROLE)
    background = None if page is None else page.to_hex()
    resolved = {
        token: colors.opaque_token(token, PAGE_ROLE)
        for tone in FILL_TONES
        for status in STATUSES
        for token in (fill_token(status, tone),)
    }
    fills = {token: color.to_hex() for token, color in resolved.items() if color is not None}
    unresolved = [token for token, color in resolved.items() if color is None]
    if background is None:
        unresolved.insert(0, PAGE_ROLE)
    darker = [
        token
        for status in STATUSES
        if background is not None
        and (token := fill_token(status, "quiet")) in fills
        and hex_to_oklch(fills[token]).lightness < hex_to_oklch(background).lightness
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
    return StatusFillReport(CHECKED_MODE, background, fills, darker, close_pairs, unresolved)
