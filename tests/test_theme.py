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
    assert resolver.resolve("{neutral.05}") == "#000000"
    assert resolver.resolve("{neutral.05@0.12}") == "rgba(0, 0, 0, 0.12)"
    assert resolver.resolve("var(--x)") == "var(--x)"


def test_resolver_requires_frontend_families() -> None:
    with pytest.raises(ValueError, match="missing families"):
        PaletteResolver({"primary": "#d97757"})


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
    path = write_support_module([build_theme(definition)], tmp_path / "ha-themes.js")
    module = path.read_text()
    assert "__FONT_STYLESHEETS__" not in module
    assert '"https://fonts.example/css"' in module
    assert "--ha-themes-brand-icon-color" in module


def test_brand_icons_follow_the_primary_role() -> None:
    theme = build_theme(minimal_definition())
    for tokens in theme.modes.values():
        assert tokens["ha-themes-brand-icon-color"] == tokens["primary-color"]
