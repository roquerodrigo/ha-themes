import pytest

from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.builder import build_theme
from ha_theme_kit.theme.definition import ThemeDefinition
from ha_theme_kit.theme.loud_fills import (
    FRONTEND_LOUD_STEPS,
    WHITE,
    build_loud_fills,
    fill_token,
    on_color_token,
    readable_loud_fill,
)
from ha_theme_kit.theme.palette_resolver import PaletteResolver
from ha_theme_kit.theme.semantic_layer import PALETTE_REFERENCE
from ha_theme_kit.theme.validation import validate_theme

PALE_PALETTE = {
    "primary": "#d97757",
    "neutral": "#7a7a7a",
    "red": "#bf4d43",
    "orange": "#d08b2c",
    "green": "#788c5d",
}
STATUS_ON_COLORS = {on_color_token(status) for status in FRONTEND_LOUD_STEPS["light"]}


def anthropic_like_scales() -> dict[str, dict[str, str]]:
    return PaletteResolver(PALE_PALETTE).scales


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_frontend_steps_match_the_captured_frontend(mode: str) -> None:
    catalog = TokenCatalog.load()
    for status, (family, resting_step, hover_step) in FRONTEND_LOUD_STEPS[mode].items():
        for state, step in (
            ("resting", resting_step),
            ("hover", hover_step),
            ("active", resting_step),
        ):
            entry = catalog.find(fill_token(status, state))
            assert entry is not None
            value = (mode == "dark" and entry.dark) or entry.light
            match = PALETTE_REFERENCE.fullmatch(value or "")
            assert match is not None, value
            assert (match["family"], match["step"]) == (family, step)


def test_white_on_the_frontend_steps_is_kept_when_it_reads() -> None:
    tokens = build_loud_fills("light", anthropic_like_scales())

    assert on_color_token("danger") not in tokens
    assert on_color_token("neutral") not in tokens


def test_a_pale_fill_takes_the_dark_on_color_and_keeps_its_steps() -> None:
    scales = anthropic_like_scales()
    tokens = build_loud_fills("light", scales)

    assert tokens[on_color_token("warning")] == scales["neutral"]["05"]
    assert tokens[fill_token("warning", "resting")] == scales["orange"]["70"]
    assert tokens[fill_token("warning", "active")] == scales["orange"]["70"]
    assert tokens[fill_token("warning", "hover")] == scales["orange"]["50"]


def test_a_fill_neither_on_color_reads_on_moves_darker_under_white() -> None:
    scales = anthropic_like_scales()
    tokens = build_loud_fills("light", scales)

    assert tokens[on_color_token("success")] == WHITE
    assert tokens[fill_token("success", "resting")] == scales["green"]["40"]
    assert tokens[fill_token("success", "hover")] == scales["green"]["30"]


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


def test_moves_go_darker_under_white_before_lighter_under_the_dark_on_color() -> None:
    fill = readable_loud_fill(GREY_SCALE, "50", "40", (WHITE, "#000000"))

    assert fill.on_color == WHITE
    assert (fill.resting_step, fill.hover_step) == ("40", "30")


def test_a_dark_on_color_moves_the_fill_lighter() -> None:
    fill = readable_loud_fill(GREY_SCALE, "50", "40", ("#000000",))

    assert (fill.resting_step, fill.hover_step) == ("60", "50")
    assert fill.readable


def test_an_unreadable_scale_falls_back_to_the_frontend_steps() -> None:
    fill = readable_loud_fill(GREY_SCALE, "50", "40", ("#7f7f7f",))

    assert (fill.resting_step, fill.hover_step, fill.on_color) == ("50", "40", "#7f7f7f")
    assert not fill.readable


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_built_loud_fills_read_in_both_modes(mode: str) -> None:
    theme = build_theme(
        ThemeDefinition(slug="loud", name="Loud", description="", palette=PALE_PALETTE)
    )

    report = validate_theme(theme, TokenCatalog.load())

    loud = [
        result
        for result in report.contrast
        if result.mode == mode and result.foreground_role in STATUS_ON_COLORS
    ]
    assert len(loud) == 12
    assert all(result.passes for result in loud)


def test_a_token_override_that_breaks_a_loud_fill_fails_validation() -> None:
    theme = build_theme(
        ThemeDefinition(
            slug="loud",
            name="Loud",
            description="",
            palette=PALE_PALETTE,
            tokens={"light": {fill_token("warning", "hover"): "#555555"}},
        )
    )

    report = validate_theme(theme, TokenCatalog.load())

    failing = [
        (result.mode, result.background_role)
        for result in report.contrast
        if result.foreground_role in STATUS_ON_COLORS and not result.passes
    ]
    assert failing == [("light", fill_token("warning", "hover"))]
    assert not report.ok
