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


SUPPORT_MODULE = THEMES_DIRECTORY.parent / "www" / "ha-themes" / "ha-themes.js"
SUPPORT_MODULE_TEMPLATE = """const fontStylesheets = {stylesheets};

const appendOnce = (selector, create) => {{
  if (!document.head.querySelector(selector)) {{
    document.head.append(create());
  }}
}};

appendOnce("style[data-ha-themes]", () => {{
  const style = document.createElement("style");
  style.dataset.haThemes = "";
  style.textContent = "body {{ font-family: var(--ha-font-family-body); }}";
  return style;
}});

for (const href of fontStylesheets) {{
  appendOnce(`link[href="${{href}}"]`, () => {{
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = href;
    return link;
  }});
}}
"""


def write_support_module(themes: list[BuiltTheme], path: Path = SUPPORT_MODULE) -> Path:
    """The frontend hard-codes the body font, so themes need this module to reach the whole UI."""
    stylesheets = sorted({theme.font_stylesheet for theme in themes if theme.font_stylesheet})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(SUPPORT_MODULE_TEMPLATE.format(stylesheets=json.dumps(stylesheets, indent=2)))
    return path
