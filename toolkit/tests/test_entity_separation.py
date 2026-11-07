from pathlib import Path

import pytest

from ha_theme_kit.color.vision import color_distance
from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.builder import build_theme
from ha_theme_kit.theme.definition import ThemeDefinition
from ha_theme_kit.theme.entity_palette import FRONTEND_NAMED_HUES
from ha_theme_kit.theme.entity_separation import (
    DISTANCE_FLOOR,
    EntitySeparationPair,
    check_entity_separation,
    competing_pairs,
)
from ha_theme_kit.theme.validation import validate_theme

THEME_SOURCES = Path(__file__).resolve().parents[2] / "themes-src"
PALETTE = {
    "primary": "#d97757",
    "neutral": "#7a7a7a",
    "red": "#bf4d43",
    "orange": "#d08b2c",
    "green": "#788c5d",
}


def theme_with(entity_colors: dict) -> ThemeDefinition:
    return ThemeDefinition(
        slug="entities",
        name="Entities",
        description="",
        palette=PALETTE,
        entity_colors=entity_colors,
    )


def test_floor_sits_just_under_the_frontend_closest_competing_pair() -> None:
    closest = min(
        color_distance(FRONTEND_NAMED_HUES[first], FRONTEND_NAMED_HUES[second])
        for first, second in competing_pairs()
    )

    assert DISTANCE_FLOOR <= closest < DISTANCE_FLOOR + 0.5


def test_pairs_shared_by_two_groups_are_checked_once() -> None:
    pairs = competing_pairs()

    assert len(pairs) == len(set(pairs))
    assert ("purple", "deep-purple") in pairs
    assert ("red", "deep-orange") in pairs


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_restyle_keeps_neighbours_apart_that_share_a_band_edge(mode: str) -> None:
    tokens = build_theme(theme_with({"chroma_cap": 0.11})).modes[mode]

    for first, second in (("purple", "deep-purple"), ("amber", "yellow")):
        distance = color_distance(tokens[f"{first}-color"], tokens[f"{second}-color"])
        assert distance >= DISTANCE_FLOOR


def test_blue_and_light_blue_need_a_pin_once_chroma_is_capped() -> None:
    report = check_entity_separation(build_theme(theme_with({})), TokenCatalog.load())

    assert {(pair.first, pair.second) for pair in report.close_pairs} == {("blue", "light-blue")}


def test_pinning_two_competing_hues_together_fails_in_both_modes() -> None:
    theme = build_theme(
        theme_with({"pinned": {"red": "{primary.50}", "deep-orange": "{primary.50}"}})
    )
    report = check_entity_separation(theme, TokenCatalog.load())
    pinned_pairs = [pair for pair in report.close_pairs if pair.first == "red"]

    assert pinned_pairs == [
        EntitySeparationPair("light", "red", "deep-orange", 0.0),
        EntitySeparationPair("dark", "red", "deep-orange", 0.0),
    ]
    assert not report.passes
    assert not validate_theme(theme, TokenCatalog.load()).ok


@pytest.mark.parametrize("source", sorted(THEME_SOURCES.glob("*.yaml")), ids=lambda path: path.stem)
def test_shipped_themes_keep_competing_hues_apart(source: Path) -> None:
    assert check_entity_separation(
        build_theme(ThemeDefinition.load(source)), TokenCatalog.load()
    ).passes
