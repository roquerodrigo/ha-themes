from pathlib import Path

import pytest
import yaml

from ha_theme_kit.inventory.catalog import TokenCatalog, TokenEntry
from ha_theme_kit.theme.builder import build_theme
from ha_theme_kit.theme.definition import ThemeDefinition
from ha_theme_kit.theme.palette_resolver import PaletteResolver
from ha_theme_kit.theme.validation import validate_theme
from ha_theme_kit.theme.writer import render_home_assistant_yaml

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
    document = yaml.safe_load(render_home_assistant_yaml(build_theme(minimal_definition()), "test"))
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
    report = validate_theme(build_theme(ThemeDefinition.load(source)), TokenCatalog.load())
    assert report.unknown_tokens == []
    assert all(result.passes for result in report.contrast)
