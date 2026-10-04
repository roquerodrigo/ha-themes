from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

import yaml

from custom_components.ha_themes.const import DOMAIN

HACS_MANIFEST = Path("hacs.json")
INTEGRATION_MANIFEST = Path(f"custom_components/{DOMAIN}/manifest.json")
RELEASE_WORKFLOW = Path(".github/workflows/release.yml")
RELEASE_PLEASE_CONFIG = Path("release-please-config.json")
RELEASE_PLEASE_MANIFEST = Path(".release-please-manifest.json")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def publish_inputs() -> dict[str, str]:
    workflow = yaml.safe_load(RELEASE_WORKFLOW.read_text())
    return workflow["jobs"]["publish"]["with"]


def test_hacs_expects_the_zip_the_release_publishes() -> None:
    hacs = read_json(HACS_MANIFEST)
    inputs = publish_inputs()
    published_name = inputs.get("filename") or f"{inputs['domain']}.zip"
    assert inputs["domain"] == DOMAIN
    assert hacs["zip_release"] is True
    assert hacs["filename"] == published_name


def test_release_please_files_exist() -> None:
    package = read_json(RELEASE_PLEASE_CONFIG)["packages"]["."]
    for extra_file in package["extra-files"]:
        assert Path(extra_file["path"]).is_file(), extra_file["path"]


def test_every_version_source_agrees_with_release_please() -> None:
    released = read_json(RELEASE_PLEASE_MANIFEST)["."]
    project = tomllib.loads(Path("pyproject.toml").read_text())["project"]
    lock = tomllib.loads(Path("uv.lock").read_text())
    locked = next(
        package for package in lock["package"] if package["name"] == project["name"]
    )
    assert read_json(INTEGRATION_MANIFEST)["version"] == released
    assert project["version"] == released
    assert locked["version"] == released
