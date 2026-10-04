from html import escape
from pathlib import Path

from playwright.sync_api import sync_playwright

from ha_theme_kit.color.palette import PALETTE_STEPS
from ha_theme_kit.theme.builder import BuiltTheme
from ha_theme_kit.theme.chart_palette import CATEGORICAL_SLOTS, CHART_COLOR_COUNT
from ha_theme_kit.theme.entity_palette import ENERGY_COLORS, FRONTEND_NAMED_HUES, NEUTRAL_NAMES
from ha_theme_kit.theme.palette_resolver import REQUIRED_FAMILIES

STYLE = """
body { margin: 0; padding: 24px; font: 13px system-ui, sans-serif;
       background: var(--background); color: var(--text); width: 1100px; }
h1 { font-size: 20px; margin: 0 0 16px; }
h2 { font-size: 14px; margin: 24px 0 8px; color: var(--text-secondary); font-weight: 600; }
.row { display: flex; flex-wrap: wrap; gap: 6px; align-items: flex-start; }
.card { background: var(--surface); border: 1px solid var(--divider); border-radius: 12px;
        padding: 12px; }
.scale { display: flex; gap: 0; margin-bottom: 4px; }
.scale div { width: 64px; height: 28px; font-size: 10px; display: flex; align-items: end;
             padding: 2px 4px; box-sizing: border-box; }
.chip { width: 122px; display: flex; gap: 8px; align-items: center; }
.dot { width: 28px; height: 28px; border-radius: 50%; flex: none; }
.chip span { font-size: 11px; line-height: 1.2; }
.series div { width: 40px; height: 40px; border-radius: 6px; font-size: 10px;
              display: flex; align-items: end; justify-content: center; color: #fff; }
.series .primary { width: 64px; height: 64px; }
"""


def _text_on(color: str) -> str:
    from ha_theme_kit.color.oklch import contrast_ratio

    return (
        "#141413" if contrast_ratio("#141413", color) > contrast_ratio("#ffffff", color) else "#fff"
    )


def render_swatch_sheet(theme: BuiltTheme, mode: str) -> str:
    tokens = {**theme.base, **theme.modes[mode]}
    roles = theme.roles[mode]
    scales = "".join(
        '<div class="scale">'
        + "".join(
            f'<div style="background:{tokens[f"ha-color-{family}-{step}"]};'
            f'color:{_text_on(tokens[f"ha-color-{family}-{step}"])}">{family} {step}</div>'
            for step in PALETTE_STEPS
        )
        + "</div>"
        for family in REQUIRED_FAMILIES
    )

    def chips(names: list[str], token_of) -> str:
        return "".join(
            f'<div class="chip"><div class="dot" style="background:{tokens[token_of(name)]}"></div>'
            f"<span>{escape(name)}<br>{tokens[token_of(name)]}</span></div>"
            for name in names
        )

    named = chips([*FRONTEND_NAMED_HUES, *NEUTRAL_NAMES[mode]], lambda name: f"{name}-color")
    energy = chips(list(ENERGY_COLORS), lambda name: name)
    series = (
        "frontend defaults"
        if "color-1" not in tokens
        else "".join(
            f'<div class="{"primary" if index <= CATEGORICAL_SLOTS else ""}" '
            f'style="background:{tokens[f"color-{index}"]}">{index}</div>'
            for index in range(1, CHART_COLOR_COUNT + 1)
        )
    )
    variables = (
        f"--background:{roles['background']};--surface:{roles['surface']};"
        f"--text:{roles['text']};--text-secondary:{roles['text_secondary']};"
        f"--divider:{roles['divider']}"
    )
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{STYLE}</style></head>
<body style="{variables}">
<h1>{escape(theme.definition.name)} · {mode}</h1>
<h2>Core palette</h2><div class="card">{scales}</div>
<h2>Entity colors (named colors behind every state color)</h2>
<div class="card row">{named}</div>
<h2>Chart series: 1-8 validated, 9-54 lighter and darker folds</h2>
<div class="card row series">{series}</div>
<h2>Energy</h2><div class="card row">{energy}</div>
</body></html>"""


def capture_swatches(theme: BuiltTheme, directory: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1148, "height": 800})
        for mode in theme.modes:
            page.set_content(render_swatch_sheet(theme, mode))
            target = directory / f"palette-{mode}.png"
            page.screenshot(path=target, full_page=True)
            written.append(target)
        browser.close()
    return written
