from ha_theme_kit.inventory.catalog import TokenCatalog, TokenEntry
from ha_theme_kit.theme.builder import build_theme
from ha_theme_kit.theme.definition import ThemeDefinition
from ha_theme_kit.theme.status_fills import (
    STATUSES,
    StatusFillPair,
    check_status_fills,
    fill_token,
)
from ha_theme_kit.theme.validation import validate_theme

FAMILIES = {"danger": "red", "warning": "orange", "success": "green"}
TONE_STEPS = {"quiet": "05", "normal": "10"}
SEED_PALETTE = {
    "primary": "#d97757",
    "neutral": "#7a7a7a",
    "red": "#bf4d43",
    "orange": "#d08b2c",
    "green": "#788c5d",
}
TUNED_PALETTE = {
    **SEED_PALETTE,
    "red": {"seed": "#bf4d43", "05": "#411c18", "10": "#4a1e1a"},
    "orange": {"seed": "#d08b2c", "05": "#422c10", "10": "#4d310c"},
    "green": {"seed": "#788c5d", "05": "#242f15", "10": "#2b3619"},
}
DARK_BACKGROUND = {"dark": {"background": "#262624"}}


def frontend_catalog() -> TokenCatalog:
    entries = [
        TokenEntry(
            name=f"--{fill_token(status, tone)}",
            layer="semantic-color",
            group="fill",
            light=f"var(--ha-color-{FAMILIES[status]}-95)",
            dark=f"var(--ha-color-{FAMILIES[status]}-{step})",
        )
        for status in STATUSES
        for tone, step in TONE_STEPS.items()
    ]
    return TokenCatalog("test", "test", "today", {entry.name: entry for entry in entries})


def theme_with(palette: dict, **overrides) -> ThemeDefinition:
    return ThemeDefinition(
        slug="status",
        name="Status",
        description="",
        palette=palette,
        roles=overrides.pop("roles", DARK_BACKGROUND),
        **overrides,
    )


def test_generated_dark_steps_fail_both_floors() -> None:
    report = check_status_fills(build_theme(theme_with(SEED_PALETTE)), frontend_catalog())

    assert report.fills[fill_token("warning", "normal")] == "#230000"
    assert report.darker_than_background == [fill_token(status, "quiet") for status in STATUSES]
    assert [(pair.tone, pair.first, pair.second) for pair in report.close_pairs] == [
        ("quiet", "danger", "warning"),
        ("normal", "danger", "warning"),
    ]
    assert not report.passes


def test_hand_tuned_dark_steps_pass() -> None:
    report = check_status_fills(build_theme(theme_with(TUNED_PALETTE)), frontend_catalog())

    assert report.darker_than_background == []
    assert report.close_pairs == []
    assert report.passes


def test_theme_overrides_of_the_fill_tokens_are_checked() -> None:
    definition = theme_with(
        TUNED_PALETTE,
        tokens={"dark": {fill_token("warning", "normal"): "var(--ha-color-red-10)"}},
    )

    report = check_status_fills(build_theme(definition), frontend_catalog())

    assert report.close_pairs == [StatusFillPair("normal", "danger", "warning", 0.0)]


def test_translucent_fills_are_composited_over_the_background() -> None:
    definition = theme_with(
        TUNED_PALETTE,
        tokens={"dark": {fill_token("success", "quiet"): "rgba(0, 0, 0, 0.2)"}},
    )

    report = check_status_fills(build_theme(definition), frontend_catalog())

    assert report.darker_than_background == [fill_token("success", "quiet")]
    assert not report.passes


def test_fills_that_do_not_resolve_to_a_color_fail() -> None:
    definition = theme_with(
        TUNED_PALETTE, tokens={"dark": {fill_token("success", "quiet"): "var(--missing)"}}
    )

    report = check_status_fills(build_theme(definition), frontend_catalog())

    assert fill_token("success", "quiet") not in report.fills
    assert report.unresolved == [fill_token("success", "quiet")]
    assert not report.passes


def test_failing_status_fills_fail_validation() -> None:
    catalog = frontend_catalog()
    theme = build_theme(theme_with(SEED_PALETTE))
    for key in theme.all_token_keys():
        catalog.tokens.setdefault(f"--{key}", TokenEntry(name=f"--{key}", layer="x", group="x"))

    report = validate_theme(theme, catalog)

    assert report.status_fills is not None
    assert not report.status_fills.passes
    assert not report.ok
