import re

import pytest

from ha_theme_kit.inventory.bundle_scan import installed_frontend_directory
from ha_theme_kit.theme.entity_palette import FRONTEND_NAMED_HUES, NEUTRAL_NAMES
from ha_theme_kit.theme.writer import SUPPORT_MODULE_SOURCE

TILE_LITERALS = (
    re.compile(r'iconColor:"(#[0-9a-fA-F]{6})"'),
    re.compile(r'class="icon-background" style="background-color:\s*(#[0-9a-fA-F]{6})'),
)


def mapped_tile_colors() -> dict[str, str]:
    source = SUPPORT_MODULE_SOURCE.read_text(encoding="utf-8")
    table = re.search(r"const ICON_TILE_ENTITY_COLORS = \{(.*?)\};", source, re.DOTALL)
    assert table is not None
    return dict(re.findall(r'"(#[0-9A-F]{6})": "([a-z-]+)"', table.group(1)))


def frontend_tile_literals() -> set[str]:
    directory = installed_frontend_directory()
    if not directory.is_dir():
        pytest.skip("the frontend package is not installed")
    literals: set[str] = set()
    for chunk in directory.glob("*.js"):
        text = chunk.read_text(encoding="utf-8", errors="replace")
        for pattern in TILE_LITERALS:
            literals.update(color.upper() for color in pattern.findall(text))
    return literals


def test_every_frontend_icon_tile_color_is_mapped() -> None:
    literals = frontend_tile_literals()
    assert literals
    assert sorted(literals - mapped_tile_colors().keys()) == []


def test_icon_tiles_map_to_named_colors_every_theme_sets() -> None:
    named_colors = FRONTEND_NAMED_HUES.keys() | NEUTRAL_NAMES["light"].keys()
    assert set(mapped_tile_colors().values()) <= named_colors
