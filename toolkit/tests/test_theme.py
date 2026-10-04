from pathlib import Path

import pytest
import yaml

from ha_theme_kit.color.oklch import hex_to_rgba
from ha_theme_kit.inventory.catalog import TokenCatalog, TokenEntry
from ha_theme_kit.theme.builder import build_theme
from ha_theme_kit.theme.definition import ThemeDefinition
from ha_theme_kit.theme.palette_resolver import PaletteResolver
from ha_theme_kit.theme.validation import validate_theme
from ha_theme_kit.theme.variants import SYSTEM_UI_FONT_STACK, theme_family
from ha_theme_kit.theme.writer import render_home_assistant_yaml, write_support_module

MINIMAL_PALETTE = {
    "primary": "#d97757",
    "neutral": "#7a7a7a",
    "red": "#dc3146",
    "orange": "#f36d00",
    "green": "#00883c",
}


def minimal_definition(**overrides) -> ThemeDefinition:
    return ThemeDefinition(
        slug="minimal",
        name="Minimal",
        description="",
        palette=overrides.pop("palette", MINIMAL_PALETTE),
        **overrides,
    )


def test_resolver_expands_references_with_alpha() -> None:
    resolver = PaletteResolver({**MINIMAL_PALETTE, "neutral": {"seed": "#7a7a7a", "05": "#000000"}})
    assert resolver.resolve("{neutral.05}", "test") == "#000000"
    assert resolver.resolve("{neutral.05@0.12}", "test") == "rgba(0, 0, 0, 0.12)"
    assert resolver.resolve("{neutral.05@.5}", "test") == "rgba(0, 0, 0, .5)"
    assert resolver.resolve("var(--x)", "test") == "var(--x)"


def test_resolver_requires_frontend_families() -> None:
    with pytest.raises(ValueError, match="missing families"):
        PaletteResolver({"primary": "#d97757"})


def test_resolver_accepts_hyphenated_family_names() -> None:
    resolver = PaletteResolver(
        {**MINIMAL_PALETTE, "light-blue": {"seed": "#6a9bcc", "40": "#123456"}}
    )
    assert resolver.resolve("{light-blue.40}", "test") == "#123456"


@pytest.mark.parametrize("family", ["Blue", "light_blue", "blue-", "5"])
def test_resolver_rejects_invalid_family_names(family: str) -> None:
    with pytest.raises(ValueError, match="must be lowercase letters joined by hyphens"):
        PaletteResolver({**MINIMAL_PALETTE, family: "#6a9bcc"})


@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("{primary.5}", r"malformed palette reference \{primary.5\}"),
        ("{Primary.50}", r"malformed palette reference \{Primary.50\}"),
        ("{neutral.05@12%}", r"malformed palette reference \{neutral.05@12%\}"),
        ("{neutral.05@1.5}", r"alpha in reference \{neutral.05@1.5\} must be between 0 and 1"),
        ("{light-blue.40}", r"unknown palette family in reference \{light-blue.40\}"),
        ("{primary.15}", r"unknown palette step in reference \{primary.15\}"),
        ("{primary.50", "unbalanced braces"),
        ("primary.50}", "unbalanced braces"),
    ],
)
def test_malformed_references_fail_the_build_with_their_location(value: str, message: str) -> None:
    with pytest.raises(ValueError, match=rf"^minimal: roles.dark.divider '.*': {message}"):
        build_theme(minimal_definition(roles={"dark": {"divider": value}}))


@pytest.mark.parametrize(
    ("overrides", "location"),
    [
        ({"tokens": {"base": {"some-token": "{primary.5}"}}}, "tokens.base.some-token"),
        ({"tokens": {"light": {"some-token": "{primary.5}"}}}, "tokens.light.some-token"),
        (
            {"entity_colors": {"pinned": {"red": "{primary.5}"}}},
            "entity_colors.pinned.red in light",
        ),
        (
            {"charts": {"series": ["{primary.5}", *["#4269d0"] * 7]}},
            "charts.series seed 1 in light",
        ),
    ],
)
def test_malformed_references_name_their_section(overrides: dict, location: str) -> None:
    with pytest.raises(ValueError, match=rf"^minimal: {location} '\{{primary.5\}}': malformed"):
        build_theme(minimal_definition(**overrides))


def test_mode_dependent_roles_never_land_in_base() -> None:
    theme = build_theme(minimal_definition(roles={"dark": {"background": "#101010"}}))
    assert "primary-background-color" not in theme.base
    assert theme.modes["dark"]["primary-background-color"] == "#101010"
    assert theme.modes["light"]["primary-background-color"].startswith("#")


def test_extra_palette_families_are_references_only() -> None:
    theme = build_theme(
        minimal_definition(
            palette={**MINIMAL_PALETTE, "blue": "#6a9bcc"},
            roles={"light": {"info": "{blue.40}"}},
        )
    )
    assert not any(key.startswith("ha-color-blue-") for key in theme.base)
    assert theme.modes["light"]["info-color"] == "#4472a0"


def test_rendered_yaml_is_a_home_assistant_theme() -> None:
    themes = [build_theme(variant) for variant in theme_family(minimal_definition())]
    document = yaml.safe_load(render_home_assistant_yaml(themes, "test"))
    assert set(document) == {"Minimal", "Minimal System UI"}
    theme = document["Minimal"]
    assert set(theme["modes"]) == {"light", "dark"}
    assert theme["ha-color-primary-50"] == "#d97757"


def test_validation_flags_tokens_missing_from_catalog() -> None:
    theme = build_theme(minimal_definition(tokens={"base": {"not-a-real-token": "1px"}}))
    known = {
        key: TokenEntry(name=f"--{key}", layer="x", group="x") for key in theme.all_token_keys()
    }
    known.pop("not-a-real-token")
    catalog = TokenCatalog("test", "test", "today", {entry.name: entry for entry in known.values()})
    assert validate_theme(theme, catalog).unknown_tokens == ["not-a-real-token"]


@pytest.mark.parametrize("source", sorted(Path("themes-src").glob("*.yaml")), ids=lambda p: p.stem)
def test_shipped_themes_validate_against_catalog(source: Path) -> None:
    catalog = TokenCatalog.load()
    for variant in theme_family(ThemeDefinition.load(source)):
        report = validate_theme(build_theme(variant), catalog)
        assert report.unknown_tokens == []
        assert all(result.passes for result in report.contrast)
        assert all(chart.passes for chart in report.charts)


def test_chrome_follows_background_unless_set() -> None:
    theme = build_theme(minimal_definition(roles={"dark": {"sidebar_background": "#000000"}}))
    light = theme.modes["light"]
    assert light["sidebar-background-color"] == light["primary-background-color"]
    assert light["app-theme-color"] == light["primary-background-color"]
    assert light["app-header-background-color"] == hex_to_rgba(
        light["primary-background-color"], 0.72
    )
    assert theme.modes["dark"]["sidebar-background-color"] == "#000000"


def test_shadows_are_flat_unless_enabled() -> None:
    assert build_theme(minimal_definition()).base["ha-card-box-shadow"] == "0 0 0 0 transparent"
    assert "ha-card-box-shadow" not in build_theme(minimal_definition(shadows=True)).base


def test_system_ui_variant_drops_web_fonts() -> None:
    definition = minimal_definition(
        typography={"body": "Poppins", "code": "Fira Code", "stylesheet": "https://fonts"}
    )
    variant = build_theme(theme_family(definition)[1])
    assert variant.definition.name == "Minimal System UI"
    assert variant.base["ha-font-family-body"] == SYSTEM_UI_FONT_STACK
    assert variant.base["ha-font-family-code"] == "Fira Code"
    assert variant.font_stylesheet is None


def test_backdrop_blur_pairs_filters_with_translucent_backgrounds() -> None:
    theme = build_theme(minimal_definition(roles={"light": {"surface": "#ffffff"}}))
    assert theme.base["ha-card-backdrop-filter"].startswith("blur(")
    assert theme.modes["light"]["ha-card-background"] == "rgba(255, 255, 255, 0.8)"
    assert theme.modes["light"]["app-theme-color"].startswith("#")


def test_backdrop_blur_can_be_disabled() -> None:
    theme = build_theme(minimal_definition(backdrop_blur=False))
    assert "ha-card-backdrop-filter" not in theme.base
    assert theme.modes["dark"]["ha-card-background"].startswith("#")


def test_support_module_is_generated_from_the_packaged_source(tmp_path: Path) -> None:
    definition = minimal_definition(typography={"stylesheet": "https://fonts.example/css"})
    module = write_support_module([build_theme(definition)], tmp_path / "ha-themes.js").read_text()
    assert "__FONT_STYLESHEETS__" not in module
    assert '"https://fonts.example/css"' in module
    assert "--ha-themes-brand-icon-color" in module


def test_brand_icons_follow_the_primary_role() -> None:
    theme = build_theme(minimal_definition())
    for tokens in theme.modes.values():
        assert tokens["ha-themes-brand-icon-color"] == tokens["primary-color"]


@pytest.mark.parametrize(
    ("roles", "message"),
    [
        (
            {"dark": {"surface": "{neutral.20@0.9}"}},
            r"minimal: dark role 'surface' .* backdrop_blur",
        ),
        (
            {"light": {"header_background": "transparent"}},
            r"minimal: light role 'header_background'",
        ),
    ],
)
def test_translucent_roles_must_be_opaque_while_blurring(roles: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        build_theme(minimal_definition(roles=roles))
    assert build_theme(minimal_definition(roles=roles, backdrop_blur=False))


def test_chart_seeds_must_resolve_to_opaque_colors() -> None:
    series = ["{neutral.50@0.5}", *["#4269d0"] * 7]
    with pytest.raises(ValueError, match=r"minimal: charts.series seed 1 \('\{neutral.50@0.5\}'\)"):
        build_theme(minimal_definition(charts={"series": series}))


@pytest.mark.parametrize(
    ("section", "message"),
    [
        (
            {"entity_colors": {"pinned": {"red": {"light": "#ff0000"}}}},
            r"bad.yaml: entity_colors.pinned.red must set exactly \['light', 'dark'\]",
        ),
        (
            {"charts": {"lightness": {"dark": [0.6]}}},
            r"bad.yaml: charts.lightness.dark must be \[minimum, maximum\], got \[0.6\]",
        ),
        (
            {"entity_colors": {"lightness": {"dim": [0.2, 0.4]}}},
            r"bad.yaml: entity_colors.lightness has unknown mode 'dim'",
        ),
    ],
)
def test_definition_load_names_the_file_and_path_of_malformed_sections(
    tmp_path: Path, section: dict, message: str
) -> None:
    source = tmp_path / "bad.yaml"
    source.write_text(yaml.safe_dump({"name": "Bad", "palette": MINIMAL_PALETTE, **section}))
    with pytest.raises(ValueError, match=message):
        ThemeDefinition.load(source)


@pytest.mark.parametrize(
    ("lightness", "message"),
    [
        ({"light": [0.8, 0.2]}, r"entity_colors.lightness.light must satisfy 0 <= minimum"),
        ({"dark": [0.5, 1.2]}, r"entity_colors.lightness.dark must satisfy .* got \[0.5, 1.2\]"),
    ],
)
def test_lightness_bands_must_be_ordered_and_in_range(
    tmp_path: Path, lightness: dict, message: str
) -> None:
    source = tmp_path / "bad.yaml"
    document = {
        "name": "Bad",
        "palette": MINIMAL_PALETTE,
        "entity_colors": {"lightness": lightness},
    }
    source.write_text(yaml.safe_dump(document))
    with pytest.raises(ValueError, match=message):
        ThemeDefinition.load(source)


@pytest.mark.parametrize("key", ["shadows", "backdrop_blur"])
def test_flags_reject_quoted_booleans(tmp_path: Path, key: str) -> None:
    source = tmp_path / "bad.yaml"
    source.write_text(yaml.safe_dump({"name": "Bad", "palette": MINIMAL_PALETTE, key: "false"}))
    with pytest.raises(ValueError, match=rf"bad.yaml: {key} must be true or false, got 'false'"):
        ThemeDefinition.load(source)


@pytest.mark.parametrize(
    ("primary", "message"),
    [
        ({"seed": "#d97757", "40": "not-a-color"}, r"palette.primary.40 must be an opaque hex"),
        (
            {"seed": "#d97757", "100": "#ffffff"},
            r"palette family 'primary' has unknown steps \['100'\]",
        ),
        ({"seed": "rgba(0, 0, 0, 0.5)"}, r"palette.primary.seed must be an opaque hex"),
        (None, r"palette.primary must be an opaque hex color, got None"),
    ],
)
def test_palette_steps_must_be_known_opaque_colors(
    tmp_path: Path, primary: object, message: str
) -> None:
    source = tmp_path / "bad.yaml"
    palette = {**MINIMAL_PALETTE, "primary": primary}
    source.write_text(yaml.safe_dump({"name": "Bad", "palette": palette}))
    with pytest.raises(ValueError, match=rf"bad.yaml: {message}"):
        ThemeDefinition.load(source)
