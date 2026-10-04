import pytest

from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.builder import BuiltTheme, build_theme
from ha_theme_kit.theme.definition import ThemeDefinition
from ha_theme_kit.theme.palette_resolver import PaletteResolver
from ha_theme_kit.theme.tinted_on_colors import (
    PALETTE_REFERENCE,
    TINTED_STATUSES,
    TINTED_TONES,
    contrast_floor,
    on_color_token,
    readable_on_color,
)
from ha_theme_kit.theme.validation import validate_theme

PALE_PALETTE = {
    "primary": "#d97757",
    "neutral": "#7a7a7a",
    "red": "#bf4d43",
    "orange": "#d08b2c",
    "green": "#788c5d",
}
TINTED_ON_COLORS = {
    on_color_token(status, tone) for status in TINTED_STATUSES for tone in TINTED_TONES
}
GREY_SCALE = {
    "05": "#111111",
    "10": "#1a1a1a",
    "20": "#222222",
    "30": "#333333",
    "40": "#555555",
    "50": "#888888",
    "60": "#aaaaaa",
    "70": "#cccccc",
    "80": "#dddddd",
    "90": "#eeeeee",
    "95": "#f8f8f8",
}


def pale_theme(tokens: dict[str, dict[str, str]] | None = None) -> BuiltTheme:
    return build_theme(
        ThemeDefinition(
            slug="tinted",
            name="Tinted",
            description="",
            palette=PALE_PALETTE,
            tokens=tokens or {},
        )
    )


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_every_tinted_on_color_is_a_palette_step_in_the_frontend(mode: str) -> None:
    catalog = TokenCatalog.load()
    for key in TINTED_ON_COLORS:
        entry = catalog.find(key)
        assert entry is not None
        value = (mode == "dark" and entry.dark) or entry.light
        assert PALETTE_REFERENCE.fullmatch(value or ""), (key, value)


def test_the_floor_is_the_frontend_ratio_where_the_frontend_misses_four_and_a_half() -> None:
    catalog = TokenCatalog.load()

    quiet = contrast_floor(
        "ha-color-on-warning-quiet", "ha-color-fill-warning-quiet-resting", catalog, "light"
    )
    normal = contrast_floor(
        "ha-color-on-warning-normal", "ha-color-fill-warning-normal-resting", catalog, "light"
    )

    assert quiet == pytest.approx(4.12, abs=0.01)
    assert normal == 4.5


def test_an_on_color_that_meets_its_floors_is_kept() -> None:
    assert readable_on_color(GREY_SCALE, "40", [("#eeeeee", 4.5)]) == "#555555"


def test_an_on_color_moves_away_from_light_backdrops_to_the_nearest_readable_step() -> None:
    assert readable_on_color(GREY_SCALE, "50", [("#eeeeee", 4.5), ("#ffffff", 4.5)]) == "#555555"


def test_an_on_color_moves_away_from_dark_backdrops() -> None:
    assert readable_on_color(GREY_SCALE, "50", [("#1a1a1a", 9.0)]) == "#cccccc"


def test_an_unreachable_floor_keeps_the_frontend_step() -> None:
    assert readable_on_color(GREY_SCALE, "50", [("#888888", 21.0)]) == "#888888"


def test_a_pale_warning_family_takes_its_text_from_darker_steps() -> None:
    scales = PaletteResolver(PALE_PALETTE).scales
    light = pale_theme().modes["light"]

    assert light[on_color_token("warning", "normal")] == scales["orange"]["30"]
    assert light[on_color_token("warning", "quiet")] == scales["orange"]["40"]
    assert on_color_token("danger", "normal") not in light


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_built_tinted_on_colors_meet_their_floors(mode: str) -> None:
    report = validate_theme(pale_theme(), TokenCatalog.load())

    tinted = [
        result
        for result in report.contrast
        if result.mode == mode and result.foreground_role in TINTED_ON_COLORS
    ]
    assert len(tinted) >= 45
    assert all(result.passes for result in tinted)


def test_a_token_override_below_the_frontend_ratio_fails_validation() -> None:
    scales = PaletteResolver(PALE_PALETTE).scales
    theme = pale_theme({"light": {on_color_token("warning", "quiet"): scales["orange"]["50"]}})

    report = validate_theme(theme, TokenCatalog.load())

    failing = {
        result.foreground_role
        for result in report.contrast
        if result.foreground_role in TINTED_ON_COLORS and not result.passes
    }
    assert failing == {on_color_token("warning", "quiet")}
    assert not report.ok
