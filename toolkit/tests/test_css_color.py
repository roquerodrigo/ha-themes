import pytest

from ha_theme_kit.color.css_color import CssColor, contrast_on, flatten, parse_css_color
from ha_theme_kit.inventory.catalog import TokenCatalog, TokenEntry
from ha_theme_kit.theme.token_colors import resolve_color_value, resolve_token_color

WHITE = CssColor(1.0, 1.0, 1.0)
BLACK = CssColor(0.0, 0.0, 0.0)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("#fff", WHITE),
        ("#FFFFFF", WHITE),
        ("#000f", BLACK),
        ("#00000000", CssColor(0.0, 0.0, 0.0, 0.0)),
        ("#ffffff80", CssColor(1.0, 1.0, 1.0, 128 / 255)),
        ("rgb(255, 255, 255)", WHITE),
        ("rgba(255, 255, 255, 0.9)", CssColor(1.0, 1.0, 1.0, 0.9)),
        ("rgba(255,255,255,.5)", CssColor(1.0, 1.0, 1.0, 0.5)),
        ("rgb(0 0 0 / 50%)", CssColor(0.0, 0.0, 0.0, 0.5)),
        ("rgb(100% 100% 100%)", WHITE),
        (" transparent ", CssColor(0.0, 0.0, 0.0, 0.0)),
    ],
)
def test_parses_hex_and_rgb_colors(value: str, expected: CssColor) -> None:
    assert parse_css_color(value) == expected


@pytest.mark.parametrize(
    "value",
    ["white", "#ff", "#fffff", "rgb(1, 2)", "hsl(0 0% 100%)", "color-mix(in srgb, red, blue)"],
)
def test_unsupported_values_do_not_parse(value: str) -> None:
    assert parse_css_color(value) is None


def test_translucent_colors_are_composited_over_an_opaque_backdrop() -> None:
    assert flatten(CssColor(0.0, 0.0, 0.0, 0.5), WHITE) == CssColor(0.5, 0.5, 0.5)
    assert flatten(CssColor(0.0, 0.0, 0.0, 0.5), None) is None
    assert flatten(CssColor(0.0, 0.0, 0.0, 0.5), CssColor(1.0, 1.0, 1.0, 0.5)) is None
    assert flatten(WHITE, None) == WHITE


def test_contrast_needs_an_opaque_background() -> None:
    assert contrast_on(parse_css_color("#fff"), parse_css_color("#fff")) == 1.0
    assert contrast_on(BLACK, WHITE) == 21.0
    assert contrast_on(parse_css_color("rgba(255, 255, 255, 0.9)"), WHITE) == 1.0
    assert contrast_on(WHITE, CssColor(0.0, 0.0, 0.0, 0.5)) is None
    assert contrast_on(None, WHITE) is None


def catalog_with(**declarations: str | None) -> TokenCatalog:
    return TokenCatalog(
        frontend_version="test",
        core_version="test",
        captured_at="test",
        tokens={
            f"--{name}": TokenEntry(name=f"--{name}", layer="test", group="test", light=value)
            for name, value in declarations.items()
        },
    )


def test_variable_chains_resolve_through_theme_and_frontend_defaults() -> None:
    catalog = catalog_with(**{"frontend-white": "#fff", "frontend-alias": "var(--frontend-white)"})
    tokens = {"theme-alias": "var(--frontend-alias)"}

    assert resolve_color_value("var(--theme-alias)", tokens, catalog, "light") == WHITE
    assert resolve_token_color("theme-alias", tokens, catalog, "light") == "#ffffff"


def test_variable_fallbacks_apply_only_to_undeclared_variables() -> None:
    catalog = catalog_with(**{"declared": "#000", "undeclared": None})

    assert resolve_color_value("var(--undeclared, #fff)", {}, catalog, "light") == WHITE
    assert resolve_color_value("var(--missing, var(--declared))", {}, catalog, "light") == BLACK
    assert resolve_color_value("var(--declared, #fff)", {}, catalog, "light") == BLACK
    assert resolve_color_value("var(--undeclared)", {}, catalog, "light") is None


def test_variable_cycles_and_translucent_tokens_do_not_resolve_to_opaque_hex() -> None:
    tokens = {"first": "var(--second)", "second": "var(--first)", "veil": "rgba(0, 0, 0, 0.5)"}
    catalog = catalog_with()

    assert resolve_color_value("var(--first)", tokens, catalog, "light") is None
    assert resolve_token_color("veil", tokens, catalog, "light") is None
