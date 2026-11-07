from dataclasses import replace
from pathlib import Path

from ha_theme_kit.color.oklch import contrast_ratio
from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.builder import build_theme
from ha_theme_kit.theme.contrast_result import ContrastResult
from ha_theme_kit.theme.definition import ThemeDefinition
from ha_theme_kit.theme.validation import validate_theme
from ha_theme_kit.theme.variants import theme_family

HIGH_CONTRAST_FIXTURE = Path(__file__).parent / "fixtures" / "high-contrast-glacier.yaml"


def failing_pairs(definition: ThemeDefinition) -> list[ContrastResult]:
    report = validate_theme(build_theme(definition), TokenCatalog.load())
    return [result for result in report.contrast if not result.passes]


def with_dark_tokens(definition: ThemeDefinition, tokens: dict[str, str]) -> ThemeDefinition:
    dark_tokens = {**definition.tokens.get("dark", {}), **tokens}
    return replace(definition, tokens={**definition.tokens, "dark": dark_tokens})


def test_the_high_contrast_fixture_validates_in_both_variants() -> None:
    catalog = TokenCatalog.load()

    for variant in theme_family(ThemeDefinition.load(HIGH_CONTRAST_FIXTURE)):
        report = validate_theme(build_theme(variant), catalog)
        assert report.ok, [result for result in report.contrast if not result.passes]


def test_a_raw_token_override_of_a_role_token_is_measured() -> None:
    definition = with_dark_tokens(
        ThemeDefinition.load(HIGH_CONTRAST_FIXTURE), {"secondary-text-color": "{neutral.30}"}
    )

    failing = {
        (result.foreground_role, result.background_role, result.foreground_token)
        for result in failing_pairs(definition)
    }

    assert failing == {
        ("text_secondary", "background", "secondary-text-color"),
        ("text_secondary", "surface", "secondary-text-color"),
    }


def test_a_raw_backdrop_override_fails_every_role_drawn_on_it() -> None:
    definition = with_dark_tokens(
        ThemeDefinition.load(HIGH_CONTRAST_FIXTURE), {"ha-card-background": "#ffffff"}
    )

    failing = failing_pairs(definition)

    assert {result.background_token for result in failing} == {"ha-card-background"}
    assert {result.foreground_role for result in failing} >= {"text", "text_secondary", "error"}


def test_a_translucent_card_is_measured_over_the_page() -> None:
    definition = ThemeDefinition(
        slug="glass",
        name="Glass",
        description="",
        palette=ThemeDefinition.load(HIGH_CONTRAST_FIXTURE).palette,
        roles={"light": {"background": "#000000", "surface": "#ffffff", "text": "#000000"}},
    )

    report = validate_theme(build_theme(definition), TokenCatalog.load())

    text_on_surface = next(
        result
        for result in report.contrast
        if result.mode == "light"
        and result.foreground_role == "text"
        and result.background_role == "surface"
    )

    assert text_on_surface.background_token == "ha-card-background"
    assert text_on_surface.ratio == round(contrast_ratio("#000000", "#cccccc"), 2)
