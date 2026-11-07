from pathlib import Path

import pytest

from ha_theme_kit.cli import THEME_SOURCES
from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.builder import BuiltTheme, build_theme
from ha_theme_kit.theme.definition import ThemeDefinition
from ha_theme_kit.theme.variants import theme_family
from ha_theme_kit.theme.writer import (
    SUPPORT_MODULE,
    THEMES_DIRECTORY,
    render_home_assistant_yaml,
    render_support_module,
)

REBUILD_HINT = "run `scripts/ha-themes build --strict` and commit the output"
THEME_SOURCE_FILES = sorted(THEME_SOURCES.glob("*.yaml"))


def build_family(source: Path) -> list[BuiltTheme]:
    return [build_theme(variant) for variant in theme_family(ThemeDefinition.load(source))]


def test_every_theme_source_is_shipped() -> None:
    assert THEME_SOURCE_FILES
    shipped = sorted(path.name for path in THEMES_DIRECTORY.glob("*.yaml"))
    assert shipped == [source.name for source in THEME_SOURCE_FILES], REBUILD_HINT


@pytest.mark.parametrize("source", THEME_SOURCE_FILES, ids=lambda path: path.stem)
def test_shipped_theme_matches_its_source(source: Path) -> None:
    rendered = render_home_assistant_yaml(
        build_family(source), TokenCatalog.load().frontend_version
    )
    shipped = (THEMES_DIRECTORY / source.name).read_bytes()
    assert shipped == rendered.encode(), f"{source.name} is stale: {REBUILD_HINT}"


def test_shipped_support_module_matches_its_source() -> None:
    rendered = render_support_module()
    assert SUPPORT_MODULE.read_bytes() == rendered.encode(), (
        f"ha-themes.js is stale: {REBUILD_HINT}"
    )
