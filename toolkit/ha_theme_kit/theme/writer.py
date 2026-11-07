import json
import re
from pathlib import Path

from ha_theme_kit.theme.builder import BuiltTheme

INTEGRATION_DIRECTORY = Path(__file__).resolve().parents[3] / "custom_components" / "ha_themes"
THEMES_DIRECTORY = INTEGRATION_DIRECTORY / "themes"
YAML_NON_PRINTABLE = re.compile("[\u007f-\u009f\u2028\u2029\ufeff\ufffe\uffff]")


def render_home_assistant_yaml(theme: BuiltTheme, source_version: str) -> str:
    lines = [
        f"# Generated from themes-src/{theme.definition.slug}.yaml for frontend {source_version}.",
        "# Do not edit by hand: run `ha-themes build`.",
        f"{_double_quoted_scalar(theme.definition.name)}:",
        *_render_block(theme.base, indent=2),
        "  modes:",
    ]
    for mode, tokens in theme.modes.items():
        lines.append(f"    {mode}:")
        lines += _render_block(tokens, indent=6)
    return "\n".join(lines) + "\n"


def _render_block(tokens: dict[str, str], indent: int) -> list[str]:
    padding = " " * indent
    return [f"{padding}{key}: {_double_quoted_scalar(value)}" for key, value in tokens.items()]


def _double_quoted_scalar(value: str) -> str:
    """Keeps non-ASCII text literal: Home Assistant's YAML loader turns JSON surrogate pair
    escapes into lone surrogates, which its JSON encoder then refuses to serialize."""
    quoted = json.dumps(value, ensure_ascii=False)
    return YAML_NON_PRINTABLE.sub(lambda match: f"\\u{ord(match.group()):04x}", quoted)


def write_theme(theme: BuiltTheme, source_version: str, directory: Path = THEMES_DIRECTORY) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{theme.definition.slug}.yaml"
    path.write_text(render_home_assistant_yaml(theme, source_version), encoding="utf-8")
    return path


SUPPORT_MODULE = INTEGRATION_DIRECTORY / "frontend" / "ha-themes.js"
SUPPORT_MODULE_SOURCE = Path(__file__).resolve().parents[1] / "support" / "ha-themes.js"


def write_support_module(path: Path = SUPPORT_MODULE) -> Path:
    """Reaches what theme variables cannot: the hard-coded body font, the web font stylesheet
    of the active theme, and the flat generic integration icons, which are bitmaps in the
    frontend's default blue.

    The integration serves it under a content-hash URL, so caches never hold a stale copy.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_support_module(), encoding="utf-8")
    return path


def render_support_module() -> str:
    return SUPPORT_MODULE_SOURCE.read_text(encoding="utf-8")
