import argparse
import sys
from pathlib import Path

from ha_theme_kit.inventory.catalog import TokenCatalog

PROJECT_ROOT = Path(__file__).resolve().parents[2]
THEME_SOURCES = PROJECT_ROOT / "themes-src"


def command_catalog(_arguments: argparse.Namespace) -> int:
    from ha_theme_kit.inventory.browser_capture import capture_runtime_tokens
    from ha_theme_kit.inventory.bundle_scan import installed_frontend_version, scan_bundle
    from ha_theme_kit.inventory.catalog import build_catalog
    from ha_theme_kit.inventory.dev_instance import DevInstance
    from ha_theme_kit.inventory.reference_docs import write_reference_docs

    runtime = capture_runtime_tokens(DevInstance.from_credentials_file())
    catalog = build_catalog(runtime, scan_bundle(), installed_frontend_version())
    catalog.save()
    for path in write_reference_docs(catalog):
        print(f"wrote {path.relative_to(PROJECT_ROOT)}")
    print(f"catalog: {len(catalog.tokens)} tokens for frontend {catalog.frontend_version}")
    return 0


def command_docs(_arguments: argparse.Namespace) -> int:
    from ha_theme_kit.inventory.reference_docs import write_reference_docs

    for path in write_reference_docs(TokenCatalog.load()):
        print(f"wrote {path.relative_to(PROJECT_ROOT)}")
    return 0


def _theme_sources(selected: list[str]) -> list[Path]:
    sources = sorted(THEME_SOURCES.glob("*.yaml"))
    if selected:
        sources = [source for source in sources if source.stem in selected]
    return sources


def command_build(arguments: argparse.Namespace) -> int:
    from ha_theme_kit.theme.builder import build_theme
    from ha_theme_kit.theme.definition import ThemeDefinition
    from ha_theme_kit.theme.validation import validate_theme
    from ha_theme_kit.theme.writer import write_font_loader, write_theme

    catalog = TokenCatalog.load()
    failed = False
    for source in _theme_sources(arguments.themes):
        theme = build_theme(ThemeDefinition.load(source))
        report = validate_theme(theme, catalog)
        path = write_theme(theme, catalog.frontend_version)
        token_count = len(theme.all_token_keys())
        print(f"{source.stem}: {token_count} tokens → {path.relative_to(PROJECT_ROOT)}")
        if font_loader := write_font_loader(theme):
            print(f"  font loader → {font_loader.relative_to(PROJECT_ROOT)}")
        for key in report.unknown_tokens:
            print(f"  ✗ unknown token {key!r} (not in frontend {catalog.frontend_version})")
        for result in report.contrast:
            mark = "✓" if result.passes else "✗"
            print(
                f"  {mark} {result.mode:5} {result.foreground_role} on {result.background_role}:"
                f" {result.ratio}:1 (min {result.minimum})"
            )
        failed = failed or not report.ok
    return 1 if failed and arguments.strict else 0


def command_preview(arguments: argparse.Namespace) -> int:
    from ha_theme_kit.inventory.dev_instance import DevInstance
    from ha_theme_kit.theme.definition import ThemeDefinition
    from ha_theme_kit.theme.preview import capture_previews

    instance = DevInstance.from_credentials_file()
    for source in _theme_sources(arguments.themes):
        definition = ThemeDefinition.load(source)
        for path in capture_previews(instance, definition.name, definition.slug):
            print(f"wrote {path.relative_to(PROJECT_ROOT)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="ha-themes")
    commands = parser.add_subparsers(required=True)

    catalog = commands.add_parser(
        "catalog", help="capture tokens from the dev instance and regenerate the reference"
    )
    catalog.set_defaults(handler=command_catalog)

    docs = commands.add_parser("docs", help="regenerate the reference from catalog/tokens.json")
    docs.set_defaults(handler=command_docs)

    build = commands.add_parser("build", help="build themes-src/*.yaml into themes/")
    build.add_argument("themes", nargs="*", help="theme slugs (default: all)")
    build.add_argument("--strict", action="store_true", help="fail on validation errors")
    build.set_defaults(handler=command_build)

    preview = commands.add_parser("preview", help="screenshot themes in Google Chrome")
    preview.add_argument("themes", nargs="*", help="theme slugs (default: all)")
    preview.set_defaults(handler=command_preview)

    arguments = parser.parse_args()
    return arguments.handler(arguments)


if __name__ == "__main__":
    sys.exit(main())
