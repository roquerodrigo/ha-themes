import argparse
from pathlib import Path

import pytest
import yaml

from ha_theme_kit import cli
from ha_theme_kit.theme import validation, writer
from ha_theme_kit.theme.chart_palette import suggest_series_orders
from ha_theme_kit.theme.validation import ValidationReport


@pytest.fixture
def theme_sources(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    document = yaml.safe_load((cli.THEME_SOURCES / "anthropic.yaml").read_text())
    document.pop("charts", None)
    (tmp_path / "chartless.yaml").write_text(yaml.safe_dump(document))
    monkeypatch.setattr(cli, "THEME_SOURCES", tmp_path)
    return tmp_path


def test_unknown_theme_slugs_are_rejected(theme_sources: Path) -> None:
    with pytest.raises(cli.UnknownThemesError, match=r"anthropc \(available: chartless\)"):
        cli._theme_sources(["chartless", "anthropc"])


def test_selected_theme_slugs_pick_their_sources(theme_sources: Path) -> None:
    assert cli._theme_sources(["chartless"]) == [theme_sources / "chartless.yaml"]


def test_order_suggestions_need_chart_series() -> None:
    assert suggest_series_orders({}) == []


def test_palette_reports_themes_without_charts(
    theme_sources: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.command_palette(argparse.Namespace(themes=[])) == 0
    assert "no charts section" in capsys.readouterr().out


def test_strict_build_writes_nothing_when_validation_fails(
    theme_sources: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    written: list[str] = []
    monkeypatch.setattr(
        validation, "validate_theme", lambda *_: ValidationReport(["--bogus"], [], [])
    )
    monkeypatch.setattr(writer, "write_theme_family", lambda *_: written.append("theme"))
    monkeypatch.setattr(writer, "write_support_module", lambda *_: written.append("module"))

    arguments = argparse.Namespace(themes=[], strict=True, verbose=False)

    assert cli.command_build(arguments) == 1
    assert written == []
