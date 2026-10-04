from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.builder import build_theme
from ha_theme_kit.theme.definition import ThemeDefinition
from ha_theme_kit.theme.form_separation import FORM_CONTRAST_FLOOR, check_form_separation
from ha_theme_kit.theme.neutral_layers import (
    FORM_BACKGROUND,
    FORM_BACKGROUND_DISABLED,
    FORM_BACKGROUND_HOVER,
    QUIET_HOVER,
    QUIET_RESTING,
    SURFACE_LOW,
)
from ha_theme_kit.theme.validation import validate_theme

PALETTE = {
    "primary": "#d97757",
    "neutral": dict(
        zip(
            ("05", "10", "20", "30", "40", "50", "60", "70", "80", "90", "95"),
            (
                *("#141414", "#202020", "#363636", "#4a4a4a", "#5e5e5e", "#7a7a7a"),
                *("#989898", "#b1b1b1", "#cccccc", "#e6e6e6", "#f3f3f3"),
            ),
            strict=True,
        )
    ),
    "red": "#bf4d43",
    "orange": "#d08b2c",
    "green": "#788c5d",
}
RAISED_DARK_ROLES = {"dark": {"background": "{neutral.10}", "surface": "{neutral.20}"}}
FRONTEND_STEPS = {
    FORM_BACKGROUND: "var(--ha-color-neutral-20)",
    FORM_BACKGROUND_DISABLED: "var(--ha-color-neutral-20)",
    FORM_BACKGROUND_HOVER: "var(--ha-color-neutral-30)",
    QUIET_RESTING: "var(--ha-color-neutral-05)",
    QUIET_HOVER: "var(--ha-color-neutral-10)",
    SURFACE_LOW: "var(--ha-color-neutral-05)",
}


def theme_with(**overrides) -> ThemeDefinition:
    return ThemeDefinition(
        slug="forms",
        name="Forms",
        description="",
        palette=PALETTE,
        roles=overrides.pop("roles", RAISED_DARK_ROLES),
        **overrides,
    )


def test_layered_raised_surface_passes() -> None:
    report = check_form_separation(build_theme(theme_with()), TokenCatalog.load())

    assert report.form_contrast is not None
    assert report.form_contrast >= FORM_CONTRAST_FLOOR
    assert report.close_pairs == []
    assert report.darker_fills == []
    assert report.passes


def test_frontend_steps_under_a_raised_surface_fail() -> None:
    theme = build_theme(theme_with(tokens={"dark": FRONTEND_STEPS}))
    report = check_form_separation(theme, TokenCatalog.load())

    assert report.form_contrast == 1.0
    assert [(first, second) for first, second, _ in report.close_pairs] == [
        (FORM_BACKGROUND, "surface"),
        (FORM_BACKGROUND_DISABLED, "surface"),
        (FORM_BACKGROUND_DISABLED, FORM_BACKGROUND),
    ]
    assert report.darker_fills == [
        (QUIET_RESTING, "background"),
        (SURFACE_LOW, "background"),
        (QUIET_HOVER, "surface"),
    ]
    assert not report.passes
    assert not validate_theme(theme, TokenCatalog.load()).ok


def test_roles_that_are_not_plain_colors_are_skipped() -> None:
    roles = {"dark": {**RAISED_DARK_ROLES["dark"], "surface": "var(--ha-color-neutral-20)"}}
    report = check_form_separation(
        build_theme(theme_with(roles=roles, backdrop_blur=False)), TokenCatalog.load()
    )

    assert "surface" not in report.colors
    assert report.form_contrast is None
