import argparse
from pathlib import Path

import pytest
import yaml

from ha_theme_kit import cli
from ha_theme_kit.theme import validation, writer
from ha_theme_kit.theme.chart_palette import suggest_series_orders
from ha_theme_kit.theme.entity_separation import EntitySeparationPair, EntitySeparationReport
from ha_theme_kit.theme.form_separation import FormSeparationReport
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
        validation, "validate_theme", lambda *_: ValidationReport(["--bogus"], [], [], [], [])
    )
    monkeypatch.setattr(writer, "write_theme_family", lambda *_: written.append("theme"))
    monkeypatch.setattr(writer, "write_support_module", lambda *_: written.append("module"))

    arguments = argparse.Namespace(themes=[], strict=True, verbose=False)

    assert cli.command_build(arguments) == 1
    assert written == []


def test_build_rejects_sources_that_share_a_theme_name(
    theme_sources: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    written: list[str] = []
    monkeypatch.setattr(writer, "write_theme_family", lambda *_: written.append("theme"))
    monkeypatch.setattr(writer, "write_support_module", lambda *_: written.append("module"))
    (theme_sources / "copy.yaml").write_text((theme_sources / "chartless.yaml").read_text())

    arguments = argparse.Namespace(themes=["copy"], strict=False, verbose=False)

    with pytest.raises(cli.DuplicateThemeNamesError) as error:
        cli.command_build(arguments)
    assert "'Anthropic' in chartless.yaml, copy.yaml" in str(error.value)
    assert "'Anthropic System UI' in chartless.yaml, copy.yaml" in str(error.value)
    assert written == []


def test_build_accepts_renamed_copies(theme_sources: Path) -> None:
    document = yaml.safe_load((theme_sources / "chartless.yaml").read_text())
    document["name"] = "My Theme"
    (theme_sources / "copy.yaml").write_text(yaml.safe_dump(document))

    cli._reject_duplicate_theme_names()


def test_entity_separation_failures_are_printed(capsys: pytest.CaptureFixture[str]) -> None:
    report = EntitySeparationReport([EntitySeparationPair("dark", "purple", "deep-purple", 0.6)])

    cli._print_entity_separation(report)
    cli._print_entity_separation(None)

    output = capsys.readouterr().out
    assert "dark  entity colors purple and deep-purple are ΔE 0.6 apart (min 5.0)" in output


def test_form_separation_failures_are_printed(capsys: pytest.CaptureFixture[str]) -> None:
    report = FormSeparationReport(
        mode="dark",
        colors={"ha-color-surface-low": "#141413", "background": "#262624"},
        form_contrast=1.03,
        close_pairs=[("ha-color-form-background", "surface", 0.4)],
        darker_fills=[("ha-color-surface-low", "background")],
    )

    cli._print_form_separation(report, verbose=False)

    output = capsys.readouterr().out
    assert "form background on surface 1.03:1 (min 1.2)" in output
    assert "ha-color-form-background and surface are ΔE 0.4 apart (min 2.0)" in output
    assert "ha-color-surface-low #141413 is darker than the background #262624" in output


def test_build_reports_pairs_it_cannot_evaluate(
    theme_sources: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    document = yaml.safe_load((theme_sources / "chartless.yaml").read_text())
    document["roles"]["light"]["text"] = "white"
    (theme_sources / "chartless.yaml").write_text(yaml.safe_dump(document))
    monkeypatch.setattr(writer, "write_theme_family", lambda *_: pytest.fail("wrote a theme"))

    arguments = argparse.Namespace(themes=[], strict=True, verbose=False)

    assert cli.command_build(arguments) == 1
    assert (
        "✗ light text on background (primary-text-color on primary-background-color): not"
        " evaluable, a side does not resolve to a color the checks can measure"
        in capsys.readouterr().out
    )


def test_outlined_form_fields_are_reported_without_a_form_contrast(
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = FormSeparationReport(
        mode="dark",
        colors={},
        form_contrast=None,
        close_pairs=[],
        darker_fills=[],
        fields_filled=False,
    )

    cli._print_form_separation(report, verbose=True)

    assert "dark  form fields outlined without a fill" in capsys.readouterr().out
