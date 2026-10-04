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
    from ha_theme_kit.theme.variants import theme_family
    from ha_theme_kit.theme.writer import write_support_module, write_theme_family

    catalog = TokenCatalog.load()
    failed = False
    for source in _theme_sources(arguments.themes):
        themes = [build_theme(variant) for variant in theme_family(ThemeDefinition.load(source))]
        path = write_theme_family(themes, catalog.frontend_version)
        print(f"{source.stem} → {path.relative_to(PROJECT_ROOT)}")
        for theme in themes:
            report = validate_theme(theme, catalog)
            print(f"  {theme.definition.name}: {len(theme.all_token_keys())} tokens")
            for key in report.unknown_tokens:
                print(f"    ✗ unknown token {key!r} (not in frontend {catalog.frontend_version})")
            for result in report.contrast:
                if arguments.verbose or not result.passes:
                    mark = "✓" if result.passes else "✗"
                    print(
                        f"    {mark} {result.mode:5} {result.foreground_role} on"
                        f" {result.background_role}: {result.ratio}:1 (min {result.minimum})"
                    )
            for chart in report.charts:
                mark = "✓" if chart.passes else "✗"
                print(
                    f"    {mark} {chart.mode:5} chart series: CVD ΔE {chart.worst_cvd_distance},"
                    f" normal ΔE {chart.worst_normal_distance}"
                    + (
                        f", lightness off-band {chart.outside_lightness_band}"
                        if chart.outside_lightness_band
                        else ""
                    )
                    + (
                        f", low chroma {chart.below_chroma_floor}"
                        if chart.below_chroma_floor
                        else ""
                    )
                    + (
                        f", sub-3:1 (legend and tooltip carry identity) {chart.below_mark_contrast}"
                        if chart.below_mark_contrast
                        else ""
                    )
                )
            if report.ok:
                print("    ✓ all tokens known, all contrast and chart checks pass")
            failed = failed or not report.ok
    every_theme = [
        build_theme(variant)
        for source in _theme_sources([])
        for variant in theme_family(ThemeDefinition.load(source))
    ]
    for path in write_support_module(every_theme):
        print(f"support module → {path.relative_to(PROJECT_ROOT)}")
    return 1 if failed and arguments.strict else 0


def command_preview(arguments: argparse.Namespace) -> int:
    from ha_theme_kit.theme.builder import build_theme
    from ha_theme_kit.theme.definition import ThemeDefinition
    from ha_theme_kit.theme.preview import PREVIEWS_DIRECTORY, capture_previews
    from ha_theme_kit.theme.swatches import capture_swatches
    from ha_theme_kit.theme.variants import theme_family

    for source in _theme_sources(arguments.themes):
        definition = ThemeDefinition.load(source)
        swatches = capture_swatches(build_theme(definition), PREVIEWS_DIRECTORY / source.stem)
        for path in swatches:
            print(f"wrote {path.relative_to(PROJECT_ROOT)}")
        if arguments.palette_only:
            continue
        from ha_theme_kit.inventory.dev_instance import DevInstance

        instance = DevInstance.from_credentials_file()
        for variant in theme_family(definition):
            for path in capture_previews(instance, variant.name, variant.slug):
                print(f"wrote {path.relative_to(PROJECT_ROOT)}")
    return 0


def command_palette(arguments: argparse.Namespace) -> int:
    from ha_theme_kit.theme.builder import build_theme
    from ha_theme_kit.theme.chart_palette import suggest_series_orders
    from ha_theme_kit.theme.definition import ThemeDefinition

    for source in _theme_sources(arguments.themes):
        definition = ThemeDefinition.load(source)
        theme = build_theme(definition)
        seeds = list(definition.charts.get("series") or [])
        print(f"{source.stem}: chart series orders that keep slot 1 (CVD ΔE, normal ΔE)")
        for cvd, normal, order in suggest_series_orders(theme.chart_series):
            labels = [seeds[index] if seeds else f"slot {index + 1}" for index in order]
            print(f"  {cvd:5} {normal:5}  {', '.join(labels)}")
        for mode in theme.modes:
            print(f"  {mode} entity colors:")
            for token, value in theme.modes[mode].items():
                if token.endswith("-color") and token.removesuffix("-color") in _named_colors():
                    print(f"    {token:24} {value}")
    return 0


def _named_colors() -> set[str]:
    from ha_theme_kit.theme.entity_palette import FRONTEND_NAMED_HUES, NEUTRAL_NAMES

    return set(FRONTEND_NAMED_HUES) | set(NEUTRAL_NAMES["light"])


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
    build.add_argument("--verbose", action="store_true", help="list every contrast check")
    build.set_defaults(handler=command_build)

    palette = commands.add_parser(
        "palette", help="suggest chart series orders and list entity colors"
    )
    palette.add_argument("themes", nargs="*", help="theme slugs (default: all)")
    palette.set_defaults(handler=command_palette)

    preview = commands.add_parser("preview", help="screenshot themes in Google Chrome")
    preview.add_argument("themes", nargs="*", help="theme slugs (default: all)")
    preview.add_argument(
        "--palette-only", action="store_true", help="only render the palette swatch sheets"
    )
    preview.set_defaults(handler=command_preview)

    arguments = parser.parse_args()
    return arguments.handler(arguments)


if __name__ == "__main__":
    sys.exit(main())
