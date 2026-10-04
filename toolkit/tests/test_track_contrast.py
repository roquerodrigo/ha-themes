import pytest

from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.builder import build_theme
from ha_theme_kit.theme.definition import ThemeDefinition
from ha_theme_kit.theme.track_contrast import (
    BACKDROP_TOKENS,
    NON_TEXT_CONTRAST_FLOOR,
    TRACK_ROLE,
    contrast_floor,
    measure_track_pairs,
)
from ha_theme_kit.theme.validation import validate_theme

PALETTE = {
    "primary": "#d97757",
    "neutral": "#7a7a7a",
    "red": "#bf4d43",
    "orange": "#d08b2c",
    "green": "#788c5d",
}


def track_definition(roles: dict[str, dict[str, str]] | None = None) -> ThemeDefinition:
    return ThemeDefinition(
        slug="tracks", name="Tracks", description="", palette=PALETTE, roles=roles or {}
    )


def track_results(roles: dict[str, dict[str, str]] | None = None) -> dict[tuple[str, str], bool]:
    report = validate_theme(build_theme(track_definition(roles)), TokenCatalog.load())
    return {
        (result.mode, result.background_role): result.passes
        for result in report.contrast
        if result.foreground_role == TRACK_ROLE
    }


def test_the_floor_is_the_frontend_ratio_where_its_light_thumb_misses_three() -> None:
    catalog = TokenCatalog.load()

    light_floors = [contrast_floor(token, catalog, "light") for token in BACKDROP_TOKENS.values()]
    dark_floors = [contrast_floor(token, catalog, "dark") for token in BACKDROP_TOKENS.values()]

    assert light_floors == [pytest.approx(1.71, abs=0.01), pytest.approx(1.78, abs=0.01)]
    assert dark_floors == [NON_TEXT_CONTRAST_FLOOR, NON_TEXT_CONTRAST_FLOOR]


def test_default_scrollbar_is_checked_on_page_and_surface_and_passes() -> None:
    assert track_results() == {
        ("light", "background"): True,
        ("light", "surface"): True,
        ("dark", "background"): True,
        ("dark", "surface"): True,
    }


def test_a_scrollbar_close_to_the_dark_surface_fails_validation() -> None:
    results = track_results({"dark": {"scrollbar": "{neutral.30}"}})

    assert results[("dark", "background")] is False
    assert results[("dark", "surface")] is False


def test_a_scrollbar_that_is_not_a_plain_color_is_not_measured() -> None:
    assert (
        measure_track_pairs(
            "dark", {"scrollbar": "var(--x)", "surface": "#202020"}, TokenCatalog.load()
        )
        == []
    )
