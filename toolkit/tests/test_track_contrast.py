import pytest

from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.builder import build_theme
from ha_theme_kit.theme.definition import ThemeDefinition
from ha_theme_kit.theme.mode_colors import ModeColors
from ha_theme_kit.theme.semantic_layer import NON_TEXT_CONTRAST_FLOOR, frontend_floor
from ha_theme_kit.theme.track_contrast import (
    BACKDROP_TOKENS,
    TRACK_ROLE,
    TRACK_TOKEN,
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


def track_definition(
    roles: dict[str, dict[str, str]] | None = None, tokens: dict[str, dict[str, str]] | None = None
) -> ThemeDefinition:
    return ThemeDefinition(
        slug="tracks",
        name="Tracks",
        description="",
        palette=PALETTE,
        roles=roles or {},
        tokens=tokens or {},
    )


def track_results(
    roles: dict[str, dict[str, str]] | None = None, tokens: dict[str, dict[str, str]] | None = None
) -> dict[tuple[str, str], bool]:
    report = validate_theme(build_theme(track_definition(roles, tokens)), TokenCatalog.load())
    return {
        (result.mode, result.background_role): result.passes
        for result in report.contrast
        if result.foreground_role == TRACK_ROLE
    }


def test_the_floor_is_the_frontend_ratio_where_its_light_thumb_misses_three() -> None:
    catalog = TokenCatalog.load()

    light_floors, dark_floors = (
        [
            frontend_floor(TRACK_TOKEN, token, NON_TEXT_CONTRAST_FLOOR, catalog, mode)
            for token in BACKDROP_TOKENS.values()
        ]
        for mode in ("light", "dark")
    )

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


def test_a_raw_scrollbar_token_is_measured_instead_of_the_role() -> None:
    results = track_results(tokens={"dark": {TRACK_TOKEN: "{neutral.30}"}})

    assert results[("dark", "background")] is False
    assert results[("dark", "surface")] is False


def test_a_scrollbar_that_does_not_resolve_is_reported_unmeasured() -> None:
    colors = ModeColors(
        "dark",
        {"background": "#141414", "surface": "#202020"},
        {TRACK_TOKEN: "var(--x)"},
        TokenCatalog.load(),
    )

    pairs = measure_track_pairs(colors)

    assert [(pair.background_role, pair.ratio) for pair in pairs] == [
        ("background", None),
        ("surface", None),
    ]
    assert not any(pair.passes for pair in pairs)


def test_a_translucent_scrollbar_is_measured_over_its_backdrop() -> None:
    colors = ModeColors(
        "dark",
        {"background": "#000000", "surface": "#000"},
        {TRACK_TOKEN: "rgba(255, 255, 255, 0.5)"},
        TokenCatalog.load(),
    )

    pairs = measure_track_pairs(colors)

    assert [pair.ratio for pair in pairs] == [5.32, 5.32]
