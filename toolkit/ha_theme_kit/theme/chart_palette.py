"""Chart colors: `color-1` … `color-54`, read by every graph, calendar and map.

The first eight are the theme's categorical series, stepped per mode into the lightness
band and chroma floor and validated for color-vision-deficiency separation. The frontend
cycles through all 54 when a chart has more series, so slots 9 to 54 repeat the eight hues at
alternating lighter and darker steps; past eight series, identity is no longer guaranteed.
"""

from dataclasses import dataclass, field
from itertools import permutations

from ha_theme_kit.color.oklch import Oklch, fit_to_gamut, hex_to_oklch, oklch_to_hex, restyle
from ha_theme_kit.color.vision import (
    CHROMA_FLOOR,
    NORMAL_VISION_FLOOR,
    worst_adjacent_cvd_distance,
    worst_adjacent_normal_distance,
)
from ha_theme_kit.theme.palette_resolver import PaletteResolver

CATEGORICAL_SLOTS = 8
CHART_COLOR_COUNT = 54
SERIES_LIGHTNESS = {"light": (0.50, 0.72), "dark": (0.58, 0.66)}
FOLD_LIGHTNESS_OFFSETS = (0.12, -0.12, 0.2, -0.18, 0.06, -0.06)
FRONTEND_SERIES = (
    "#4269d0",
    "#f4bd4a",
    "#ff725c",
    "#6cc5b0",
    "#a463f2",
    "#ff8ab7",
    "#9c6b4e",
    "#97bbf5",
)


@dataclass(frozen=True)
class ChartSettings:
    series: tuple[str, ...] = FRONTEND_SERIES
    chroma_floor: float = CHROMA_FLOOR + 0.005
    lightness: dict[str, tuple[float, float]] = field(
        default_factory=lambda: dict(SERIES_LIGHTNESS)
    )

    @classmethod
    def from_document(cls, document: dict | None) -> ChartSettings | None:
        """Without a `charts` section the frontend's own series stay in place: stepping
        them into the band compresses their lightness and collapses their separation."""
        if not document:
            return None
        series = tuple(document.get("series") or FRONTEND_SERIES)
        if len(series) != CATEGORICAL_SLOTS:
            raise ValueError(f"charts.series needs exactly {CATEGORICAL_SLOTS} colors")
        defaults = cls()
        lightness = {mode: tuple(band) for mode, band in (document.get("lightness") or {}).items()}
        return cls(series, defaults.chroma_floor, {**defaults.lightness, **lightness})


def series_for_mode(settings: ChartSettings, resolver: PaletteResolver, mode: str) -> list[str]:
    return [
        restyle(resolver.resolve(seed), settings.lightness[mode], (settings.chroma_floor, 1.0))
        for seed in settings.series
    ]


def build_chart_colors(series: list[str]) -> dict[str, str]:
    colors = list(series)
    for offset in FOLD_LIGHTNESS_OFFSETS:
        for color in series:
            base = hex_to_oklch(color)
            lightness = min(max(base.lightness + offset, 0.3), 0.9)
            colors.append(oklch_to_hex(fit_to_gamut(Oklch(lightness, base.chroma, base.hue))))
    return {f"color-{index}": color for index, color in enumerate(colors[:CHART_COLOR_COUNT], 1)}


def suggest_series_orders(
    series_by_mode: dict[str, list[str]], limit: int = 5
) -> list[tuple[float, float, list[int]]]:
    """Rank orders that keep slot 1 and clear the normal-vision floor in every mode."""
    ranked = []
    for rest in permutations(range(1, CATEGORICAL_SLOTS)):
        order = [0, *rest]
        palettes = [[colors[index] for index in order] for colors in series_by_mode.values()]
        normal = min(worst_adjacent_normal_distance(palette) for palette in palettes)
        if normal < NORMAL_VISION_FLOOR:
            continue
        cvd = min(worst_adjacent_cvd_distance(palette) for palette in palettes)
        ranked.append((round(cvd, 1), round(normal, 1), order))
    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return ranked[:limit]
