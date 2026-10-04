from pathlib import Path

from ha_theme_kit.inventory.bundle_scan import read_host_declarations, scan_bundle
from ha_theme_kit.inventory.catalog import TokenCatalog, TokenEntry
from ha_theme_kit.inventory.reference_docs import render_component_reference

CHUNK = (
    "const styles=css`:host{display:block;--control-button-background-color:var(--disabled-color);"
    "--mdc-icon-size:20px !important}:host([disabled]){--mdc-icon-size:12px}"
    "ha-icon{--mdc-icon-size:16px}"
    ".button{background:var(--control-button-background-color);"
    "width:var(--mdc-icon-size,24px);color:var(--unset-hook,red)}`;"
    "const other=css`:host{--declared-but-unread:1px;--interpolated:${size}px}`;"
)


def test_host_declarations_cover_plain_host_rules_only() -> None:
    assert read_host_declarations(CHUNK) == [
        ("--control-button-background-color", "var(--disabled-color)"),
        ("--mdc-icon-size", "20px"),
        ("--declared-but-unread", "1px"),
    ]


def test_scan_records_host_values_for_hooks_that_are_read(tmp_path: Path) -> None:
    (tmp_path / "chunk.js").write_text(CHUNK)
    usage = scan_bundle(tmp_path).usage
    assert usage["--control-button-background-color"].host_values == {"var(--disabled-color)"}
    assert usage["--mdc-icon-size"].host_values == {"20px"}
    assert usage["--unset-hook"].host_values == set()
    assert "--declared-but-unread" not in usage


def test_component_reference_marks_hooks_set_on_host() -> None:
    catalog = TokenCatalog(
        frontend_version="1",
        core_version="1",
        captured_at="2026-10-04",
        tokens={
            "--mdc-icon-size": TokenEntry(
                name="--mdc-icon-size",
                layer="component",
                group="mdc",
                consumers=2,
                fallbacks=["24px"],
                host_values=["20px"],
            ),
            "--unset-hook": TokenEntry(
                name="--unset-hook", layer="component", group="mdc", consumers=1
            ),
        },
    )
    reference = render_component_reference(catalog)
    assert "| `--mdc-icon-size` | `24px` | `20px` | 2 |" in reference
    assert "| `--unset-hook` |  |  | 1 |" in reference
