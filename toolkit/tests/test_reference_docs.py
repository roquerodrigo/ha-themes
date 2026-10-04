from ha_theme_kit.inventory.catalog import TokenCatalog, TokenEntry
from ha_theme_kit.inventory.reference_docs import (
    DOCS_DIRECTORY,
    find_broken_references,
    render_global_reference,
)
from ha_theme_kit.theme.roles import UPSTREAM_FIXES


def catalog_of(*entries: TokenEntry) -> TokenCatalog:
    return TokenCatalog("test", "test", "today", {entry.name: entry for entry in entries})


def test_undeclared_references_are_broken() -> None:
    entry = TokenEntry(name="--a", layer="x", group="x", light="var(--b)", dark="var(--missing)")
    catalog = catalog_of(entry, TokenEntry(name="--b", layer="x", group="x", light="1px"))

    assert find_broken_references(catalog) == [(entry, "dark", "`--missing` is never declared")]


def test_values_with_stray_css_syntax_are_broken() -> None:
    entry = TokenEntry(
        name="--a",
        layer="x",
        group="x",
        light="var(--b)",
        dark="var(--b)@layer wa-utilities{@supports (scrollbar-gutter",
    )
    catalog = catalog_of(entry, TokenEntry(name="--b", layer="x", group="x", light="1px"))

    assert find_broken_references(catalog) == [(entry, "dark", "malformed value")]
    assert "| `--a` | dark | malformed value |" in render_global_reference(catalog)


def test_every_broken_default_in_the_catalog_has_an_upstream_fix() -> None:
    unfixed = [
        (entry.name, mode, problem)
        for entry, mode, problem in find_broken_references(TokenCatalog.load())
        if entry.theme_key not in UPSTREAM_FIXES.get(mode, {})
    ]

    assert unfixed == []


def test_theming_guide_names_the_captured_versions() -> None:
    catalog = TokenCatalog.load()
    guide = (DOCS_DIRECTORY / "theming-guide.md").read_text()

    assert f"frontend `{catalog.frontend_version}` / Core `{catalog.core_version}`" in guide
    assert f"## Known upstream issues (frontend {catalog.frontend_version})" in guide
