import importlib.metadata
import json
from pathlib import Path

import homeassistant.components.frontend
from packaging.requirements import Requirement

from ha_theme_kit.cli import PROJECT_ROOT
from ha_theme_kit.inventory.bundle_scan import installed_frontend_version
from ha_theme_kit.inventory.catalog import TokenCatalog

BUMP_HINT = (
    "homeassistant, home-assistant-frontend and pytest-homeassistant-custom-component move "
    "together with a catalog re-capture (README: Updating to a new Home Assistant release)"
)


def installed_core_version() -> str:
    return importlib.metadata.version("homeassistant")


def find_requirement(requirements: list[str], name: str) -> Requirement:
    return next(
        requirement for requirement in map(Requirement, requirements) if requirement.name == name
    )


def test_installed_frontend_is_the_one_the_core_pins() -> None:
    manifest_file = Path(homeassistant.components.frontend.__file__).parent / "manifest.json"
    requirements = json.loads(manifest_file.read_text())["requirements"]
    pin = find_requirement(requirements, "home-assistant-frontend")
    assert installed_frontend_version() in pin.specifier, BUMP_HINT


def test_test_harness_targets_the_installed_core() -> None:
    requirements = importlib.metadata.requires("pytest-homeassistant-custom-component") or []
    pin = find_requirement(requirements, "homeassistant")
    assert installed_core_version() in pin.specifier, BUMP_HINT


def test_hacs_manifest_requires_the_installed_core() -> None:
    manifest = json.loads((PROJECT_ROOT / "hacs.json").read_text())
    assert manifest["homeassistant"] == installed_core_version(), BUMP_HINT


def test_catalog_was_captured_from_the_installed_frontend() -> None:
    catalog = TokenCatalog.load()
    assert catalog.frontend_version == installed_frontend_version(), BUMP_HINT
    assert catalog.core_version == installed_core_version(), BUMP_HINT
