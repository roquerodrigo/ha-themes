from __future__ import annotations

import json
from pathlib import Path

import pytest

TRANSLATIONS = Path("custom_components/ha_themes/translations")


def flatten_keys(tree: dict, prefix: str = "") -> set[str]:
    keys = set()
    for key, value in tree.items():
        path = f"{prefix}.{key}" if prefix else key
        keys |= flatten_keys(value, path) if isinstance(value, dict) else {path}
    return keys


@pytest.mark.parametrize(
    "locale",
    sorted(path.stem for path in TRANSLATIONS.glob("*.json") if path.stem != "en"),
)
def test_locales_share_the_english_keys(locale: str) -> None:
    english = json.loads((TRANSLATIONS / "en.json").read_text())
    other = json.loads((TRANSLATIONS / f"{locale}.json").read_text())
    assert flatten_keys(other) == flatten_keys(english)
