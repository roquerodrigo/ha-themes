import json
from pathlib import Path

from ha_theme_kit.theme.builder import BuiltTheme

THEMES_DIRECTORY = Path(__file__).resolve().parents[3] / "themes"


def render_home_assistant_yaml(theme: BuiltTheme, source_version: str) -> str:
    definition = theme.definition
    lines = [
        f"# {definition.name} — generated from themes-src/{definition.slug}.yaml"
        f" for frontend {source_version}.",
        "# Do not edit by hand: run `ha-themes build`.",
        f"{json.dumps(definition.name)}:",
    ]
    lines += _render_block(theme.base, indent=2)
    lines.append("  modes:")
    for mode, tokens in theme.modes.items():
        lines.append(f"    {mode}:")
        lines += _render_block(tokens, indent=6)
    return "\n".join(lines) + "\n"


def _render_block(tokens: dict[str, str], indent: int) -> list[str]:
    padding = " " * indent
    return [f"{padding}{key}: {json.dumps(value)}" for key, value in tokens.items()]


def write_theme(theme: BuiltTheme, source_version: str, directory: Path = THEMES_DIRECTORY) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{theme.definition.slug}.yaml"
    path.write_text(render_home_assistant_yaml(theme, source_version))
    return path


FONT_LOADER_DIRECTORY = THEMES_DIRECTORY.parent / "www" / "ha-themes"
FONT_LOADER_TEMPLATE = """const stylesheet = {stylesheet};

if (!document.head.querySelector(`link[href="${{stylesheet}}"]`)) {{
  const link = document.createElement("link");
  link.rel = "stylesheet";
  link.href = stylesheet;
  document.head.append(link);
}}
"""


def write_font_loader(theme: BuiltTheme, directory: Path = FONT_LOADER_DIRECTORY) -> Path | None:
    if not theme.font_stylesheet:
        return None
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{theme.definition.slug}-fonts.js"
    path.write_text(FONT_LOADER_TEMPLATE.format(stylesheet=json.dumps(theme.font_stylesheet)))
    return path
