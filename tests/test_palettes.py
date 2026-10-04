import pytest

from ha_theme_kit.color.oklch import hex_to_oklch
from ha_theme_kit.color.vision import check_categorical
from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.chart_palette import (
    CHART_COLOR_COUNT,
    ChartSettings,
    build_chart_colors,
    suggest_series_orders,
)
from ha_theme_kit.theme.entity_palette import (
    FRONTEND_NAMED_HUES,
    EntityColorSettings,
    build_entity_colors,
)
from ha_theme_kit.theme.palette_resolver import PaletteResolver

PALETTE = {
    "primary": "#d97757",
    "neutral": "#7a7a7a",
    "red": "#dc3146",
    "orange": "#f36d00",
    "green": "#00883c",
    "blue": "#6a9bcc",
}
REFERENCE_SERIES = [
    "#2a78d6",
    "#eb6834",
    "#1baf7a",
    "#eda100",
    "#e87ba4",
    "#008300",
    "#4a3aa7",
    "#e34948",
]


def expand_short_hex(value: str) -> str:
    digits = value.lstrip("#")
    return "#" + ("".join(digit * 2 for digit in digits) if len(digits) == 3 else digits)


def test_named_hue_defaults_match_the_captured_frontend() -> None:
    catalog = TokenCatalog.load()
    for name, default in FRONTEND_NAMED_HUES.items():
        assert expand_short_hex(catalog.find(f"{name}-color").light) == default


def test_vision_checks_reproduce_reference_measurements() -> None:
    report = check_categorical(REFERENCE_SERIES, "light", "#fcfcfb")
    assert (report.worst_cvd_distance, report.worst_normal_distance) == (9.1, 19.6)
    assert report.below_mark_contrast == ["#1baf7a", "#eda100", "#e87ba4"]


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_entity_colors_respect_the_mode_band_unless_pinned(mode: str) -> None:
    settings = EntityColorSettings(chroma_cap=0.11, pinned={"blue": "{blue.50}"})
    tokens = build_entity_colors(settings, PaletteResolver(PALETTE), mode)
    lower, upper = settings.lightness[mode]
    for name in FRONTEND_NAMED_HUES:
        color = hex_to_oklch(tokens[f"{name}-color"])
        if name != "blue":
            assert lower - 0.01 <= color.lightness <= upper + 0.01
            assert color.chroma <= 0.11 + 0.005
    assert tokens["blue-color"] == "#6a9bcc"
    assert tokens["energy-grid-consumption-color"] == tokens["blue-color"]
    assert tokens["weather-icon-sun-color"] == tokens["amber-color"]


def test_chart_colors_fill_every_frontend_slot_with_hex() -> None:
    colors = build_chart_colors(REFERENCE_SERIES)
    assert len(colors) == CHART_COLOR_COUNT
    assert colors["color-1"] == REFERENCE_SERIES[0]
    assert all(value.startswith("#") and len(value) == 7 for value in colors.values())


def test_order_suggestions_keep_the_opening_series() -> None:
    suggestions = suggest_series_orders({"light": REFERENCE_SERIES}, limit=3)
    assert suggestions
    assert all(order[0] == 0 for _, _, order in suggestions)


def test_chart_settings_require_eight_series() -> None:
    with pytest.raises(ValueError, match="exactly 8"):
        ChartSettings.from_document({"series": ["#000000"]})


def test_themes_without_charts_keep_the_frontend_series() -> None:
    assert ChartSettings.from_document(None) is None
