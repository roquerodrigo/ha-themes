from ha_theme_kit.cli import THEME_SOURCES
from ha_theme_kit.color.oklch import contrast_ratio
from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.builder import build_theme
from ha_theme_kit.theme.definition import ThemeDefinition
from ha_theme_kit.theme.toast_colors import (
    FRONTEND_TEXT_TOKEN,
    TOAST_ACTION_TOKEN,
    TOAST_BACKGROUND_TOKEN,
    TOAST_TEXT_TOKEN,
    build_toast_colors,
)
from ha_theme_kit.theme.validation import validate_theme

DARK_TOAST = "#1f1e1d"
SCALES = {
    "neutral": {"05": "#141413"},
    "primary": {
        "05": "#21120c",
        "10": "#331a10",
        "20": "#5e2a18",
        "30": "#9c4a2e",
        "40": "#c6613f",
        "50": "#d97757",
        "60": "#e89378",
        "70": "#f7b099",
        "80": "#ffccba",
        "90": "#ffe9db",
        "95": "#fff7ec",
    },
}


def anthropic() -> ThemeDefinition:
    return ThemeDefinition.load(THEME_SOURCES / "anthropic.yaml")


def toast_results(definition: ThemeDefinition) -> dict[tuple[str, str], float | None]:
    report = validate_theme(build_theme(definition), TokenCatalog.load())
    return {
        (result.mode, result.foreground_role): result.ratio
        for result in report.contrast
        if result.background_role == TOAST_BACKGROUND_TOKEN
    }


def test_frontend_toast_colors_need_no_tokens() -> None:
    for mode in ("light", "dark"):
        assert build_toast_colors(mode, {}, SCALES) == {}


def test_dark_message_text_on_the_dark_toast_turns_white() -> None:
    tokens = {TOAST_BACKGROUND_TOKEN: DARK_TOAST, FRONTEND_TEXT_TOKEN: "#141413"}

    toast_colors = build_toast_colors("dark", tokens, SCALES)

    assert toast_colors[TOAST_TEXT_TOKEN] == "#ffffff"


def test_action_moves_to_the_nearest_primary_step_that_reads_on_the_toast() -> None:
    tokens = {TOAST_BACKGROUND_TOKEN: DARK_TOAST, "ha-color-primary-40": "#c6613f"}

    toast_colors = build_toast_colors("light", tokens, SCALES)

    assert toast_colors[TOAST_ACTION_TOKEN] == "#d97757"
    assert contrast_ratio(toast_colors[TOAST_ACTION_TOKEN], DARK_TOAST) >= 4.5


def test_anthropic_toast_message_and_action_read_in_both_modes() -> None:
    results = toast_results(anthropic())

    assert set(results) == {
        (mode, token)
        for mode in ("light", "dark")
        for token in (TOAST_TEXT_TOKEN, TOAST_ACTION_TOKEN)
    }
    assert all(ratio is not None and ratio >= 4.5 for ratio in results.values())


def test_validation_reports_a_toast_color_set_by_the_theme_that_does_not_read() -> None:
    definition = anthropic()
    unreadable = ThemeDefinition(
        slug=definition.slug,
        name=definition.name,
        description=definition.description,
        palette=definition.palette,
        roles=definition.roles,
        tokens={"dark": {TOAST_TEXT_TOKEN: "{neutral.05}"}},
    )

    ratio = toast_results(unreadable)[("dark", TOAST_TEXT_TOKEN)]

    assert ratio is not None
    assert ratio < 1.5
