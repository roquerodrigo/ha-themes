import pytest

from ha_theme_kit.color.oklch import contrast_ratio, hex_to_oklch
from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.builder import build_theme
from ha_theme_kit.theme.definition import ThemeDefinition
from ha_theme_kit.theme.neutral_layers import (
    FORM_BACKGROUND,
    FORM_BACKGROUND_DISABLED,
    FORM_BACKGROUND_HOVER,
    FRONTEND_LAYERING,
    FRONTEND_NEUTRALS,
    QUIET_ACTIVE,
    QUIET_HOVER,
    QUIET_RESTING,
    SURFACE_LOW,
)
from ha_theme_kit.theme.roles import UPSTREAM_FIXES

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
FRONTEND_ANCHOR_TOKENS = {
    "background": "primary-background-color",
    "surface": "card-background-color",
}


def theme_with(roles: dict) -> ThemeDefinition:
    return ThemeDefinition(
        slug="layers", name="Layers", description="", palette=PALETTE, roles=roles
    )


def lightness(color: str) -> float:
    return hex_to_oklch(color).lightness


def full_hex(color: str) -> str:
    digits = color.lstrip("#")
    return "#" + (digits if len(digits) == 6 else "".join(digit * 2 for digit in digits)).lower()


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_frontend_layering_matches_the_catalog(mode: str) -> None:
    catalog = TokenCatalog.load()
    layering = FRONTEND_LAYERING[mode]
    for role, token in FRONTEND_ANCHOR_TOKENS.items():
        entry = catalog.find(token)
        assert entry is not None
        resolved = entry.resolved_dark if mode == "dark" else entry.resolved_light
        assert full_hex(resolved or "") == layering.anchors[role]
    for token, (_, step) in layering.steps.items():
        entry = catalog.find(token)
        assert entry is not None
        value = entry.dark if mode == "dark" else entry.light
        if mode == "dark" and token == QUIET_ACTIVE:
            assert value == "var(--ha-color-neutral-00)"
            assert UPSTREAM_FIXES["dark"][token] == f"{{neutral.{step}}}"
            continue
        assert value == f"var(--ha-color-neutral-{step})"
    for step, color in FRONTEND_NEUTRALS.items():
        entry = catalog.find(f"ha-color-neutral-{step}")
        assert entry is not None
        assert full_hex(entry.resolved_light or "") == color


def test_roles_left_where_the_frontend_puts_them_keep_its_steps() -> None:
    theme = build_theme(theme_with({"light": {"background": "#fafafa"}}))

    assert not {*FRONTEND_LAYERING["light"].steps} & theme.modes["light"].keys()
    assert {*FRONTEND_LAYERING["dark"].steps} & theme.modes["dark"].keys() == {
        FORM_BACKGROUND_DISABLED,
        QUIET_ACTIVE,
    }
    assert theme.modes["dark"]["input-fill-color"] == theme.roles["dark"]["input_fill"]


def test_a_raised_dark_surface_lifts_fields_and_hover_fills_with_it() -> None:
    theme = build_theme(theme_with(RAISED_DARK_ROLES))
    tokens, roles = theme.modes["dark"], theme.roles["dark"]
    surface, background = roles["surface"], roles["background"]

    assert contrast_ratio(tokens[FORM_BACKGROUND], surface) >= 1.3
    assert lightness(tokens[FORM_BACKGROUND_HOVER]) > lightness(tokens[FORM_BACKGROUND])
    assert lightness(tokens[QUIET_HOVER]) >= lightness(surface)
    for token in (QUIET_RESTING, QUIET_ACTIVE, SURFACE_LOW):
        assert lightness(background) <= lightness(tokens[token]) < lightness(surface)
    assert tokens["input-fill-color"] == tokens[FORM_BACKGROUND]


def test_disabled_fields_sit_between_the_surface_and_enabled_fields() -> None:
    tokens = build_theme(theme_with(RAISED_DARK_ROLES)).modes["dark"]
    surface = tokens["ha-color-surface-default"]

    assert (
        lightness(surface)
        < lightness(tokens[FORM_BACKGROUND_DISABLED])
        < lightness(tokens[FORM_BACKGROUND])
    )


def test_layered_fills_take_the_hue_of_the_theme_neutrals() -> None:
    warm = {**PALETTE, "neutral": "#87867f"}
    definition = ThemeDefinition(
        slug="warm", name="Warm", description="", palette=warm, roles=RAISED_DARK_ROLES
    )
    form = hex_to_oklch(build_theme(definition).modes["dark"][FORM_BACKGROUND])

    assert form.chroma > 0.003
    assert abs(form.hue - hex_to_oklch("#87867f").hue) < 15


def test_a_theme_input_fill_wins_over_the_layered_form_background() -> None:
    roles = {"dark": {**RAISED_DARK_ROLES["dark"], "input_fill": "#123456"}}
    theme = build_theme(theme_with(roles))

    assert theme.modes["dark"]["input-fill-color"] == "#123456"


def test_theme_tokens_still_override_layered_fills() -> None:
    definition = theme_with(RAISED_DARK_ROLES)
    definition = ThemeDefinition(
        slug=definition.slug,
        name=definition.name,
        description="",
        palette=PALETTE,
        roles=RAISED_DARK_ROLES,
        tokens={"dark": {FORM_BACKGROUND: "#010101"}},
    )

    assert build_theme(definition).modes["dark"][FORM_BACKGROUND] == "#010101"
