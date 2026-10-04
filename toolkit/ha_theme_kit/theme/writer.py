import json
from pathlib import Path

from ha_theme_kit.theme.builder import BuiltTheme

INTEGRATION_DIRECTORY = Path(__file__).resolve().parents[3] / "custom_components" / "ha_themes"
THEMES_DIRECTORY = INTEGRATION_DIRECTORY / "themes"


def render_home_assistant_yaml(themes: list[BuiltTheme], source_version: str) -> str:
    source_slug = themes[0].definition.slug
    lines = [
        f"# Generated from themes-src/{source_slug}.yaml for frontend {source_version}.",
        "# Do not edit by hand: run `ha-themes build`.",
    ]
    for theme in themes:
        lines.append(f"{json.dumps(theme.definition.name)}:")
        lines += _render_block(theme.base, indent=2)
        lines.append("  modes:")
        for mode, tokens in theme.modes.items():
            lines.append(f"    {mode}:")
            lines += _render_block(tokens, indent=6)
    return "\n".join(lines) + "\n"


def _render_block(tokens: dict[str, str], indent: int) -> list[str]:
    padding = " " * indent
    return [f"{padding}{key}: {json.dumps(value)}" for key, value in tokens.items()]


def write_theme_family(
    themes: list[BuiltTheme], source_version: str, directory: Path = THEMES_DIRECTORY
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{themes[0].definition.slug}.yaml"
    path.write_text(render_home_assistant_yaml(themes, source_version))
    return path


SUPPORT_MODULE = INTEGRATION_DIRECTORY / "frontend" / "ha-themes.js"
SUPPORT_MODULE_SOURCE = Path(__file__).resolve().parents[1] / "support" / "ha-themes.js"


def write_support_module(themes: list[BuiltTheme], path: Path = SUPPORT_MODULE) -> Path:
    """Reaches what theme variables cannot: the hard-coded body font, web fonts, and the
    flat generic integration icons, which are bitmaps in the frontend's default blue.

    The integration serves it under a content-hash URL, so caches never hold a stale copy.
    """
    stylesheets = sorted({theme.font_stylesheet for theme in themes if theme.font_stylesheet})
    module = SUPPORT_MODULE_SOURCE.read_text()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(module.replace("__FONT_STYLESHEETS__", json.dumps(stylesheets, indent=2)))
    return path
