import re

import pytest

from ha_theme_kit.inventory.bundle_scan import installed_frontend_directory

CHART_THEME = re.compile(r'_createTheme\(\w+\)\{.{0,400}?textStyle:\{[^}]*fontFamily:"([^"]*)"')
EDITOR_LITERALS = re.compile(r'"\.(cm-completionDetail|cm-textfield)":\{[^}]*fontFamily:"([^"]*)"')


def frontend_text() -> str:
    directory = installed_frontend_directory()
    if not directory.is_dir():
        pytest.skip("the frontend package is not installed")
    return "".join(
        chunk.read_text(encoding="utf-8", errors="replace") for chunk in directory.glob("*.js")
    )


def test_charts_still_register_a_literal_font_in_create_theme() -> None:
    fonts = set(CHART_THEME.findall(frontend_text()))
    assert fonts == {"Roboto, Noto, sans-serif"}, (
        "ha-chart-base changed how it sets the chart font; review the chart patch in the "
        "support module"
    )


def test_code_editor_still_sets_roboto_on_the_patched_selectors() -> None:
    assert set(EDITOR_LITERALS.findall(frontend_text())) == {
        ("cm-completionDetail", "Roboto"),
        ("cm-textfield", "Roboto"),
    }
