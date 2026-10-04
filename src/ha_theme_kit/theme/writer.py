import hashlib
import json
from pathlib import Path

from ha_theme_kit.theme.builder import BuiltTheme

THEMES_DIRECTORY = Path(__file__).resolve().parents[3] / "themes"


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


SUPPORT_DIRECTORY = THEMES_DIRECTORY.parent / "www" / "ha-themes"
SUPPORT_SOURCES = Path(__file__).resolve().parents[1] / "support"
SUPPORT_LOADER = "ha-themes-loader.js"
SUPPORT_MODULE = "ha-themes.js"
SUPPORT_VERSION = "ha-themes.version.json"


def write_support_module(
    themes: list[BuiltTheme], directory: Path = SUPPORT_DIRECTORY
) -> list[Path]:
    """Reaches what theme variables cannot: the hard-coded body font, web fonts, and the
    flat generic integration icons, which are bitmaps in the frontend's default blue.

    The module is registered through a loader that never changes and imports the build by
    content hash, since Home Assistant serves /local with a long-lived cache.
    """
    stylesheets = sorted({theme.font_stylesheet for theme in themes if theme.font_stylesheet})
    module = (SUPPORT_SOURCES / SUPPORT_MODULE).read_text()
    module = module.replace("__FONT_STYLESHEETS__", json.dumps(stylesheets, indent=2))
    directory.mkdir(parents=True, exist_ok=True)
    outputs = {
        directory / SUPPORT_LOADER: (SUPPORT_SOURCES / SUPPORT_LOADER).read_text(),
        directory / SUPPORT_MODULE: module,
        directory / SUPPORT_VERSION: json.dumps(
            {"hash": hashlib.sha256(module.encode()).hexdigest()[:12]}
        )
        + "\n",
    }
    for path, content in outputs.items():
        path.write_text(content)
    return list(outputs)
