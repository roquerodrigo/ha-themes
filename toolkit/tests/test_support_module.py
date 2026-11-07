import io
import shutil
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from PIL import Image
from playwright.sync_api import Browser, Page, Route, sync_playwright
from playwright.sync_api import Error as PlaywrightError

from ha_theme_kit.theme.writer import SUPPORT_MODULE_SOURCE, render_support_module

ORIGIN = "http://ha-themes.test"
CROSS_ORIGIN = "http://cross-origin.test"
GENERIC_ICON = "/api/brands/integration/generic/icon.png"
OTHER_GENERIC_ICON = "/api/brands/integration/other_generic/icon.png"
LOGO = "/api/brands/integration/logo/icon.png"
REPLACEMENT_IMAGE = "/replacement.png"
FONT_STYLESHEET = "/fonts/theme.css"
GENERIC_ICON_RGB = (0, 171, 248)
RED = (255, 0, 0)
GREEN = (0, 128, 0)
BLUE = (0, 0, 255)
SETTLE_MILLISECONDS = 300
WAIT_SECONDS = 5

PAGE_HTML = """<!doctype html>
<html><head><script type="module" src="/ha-themes.js"></script></head><body></body></html>"""

HELPERS = """() => {
window.addIcon = (id, src, { parent = document.body, shadowHost = false } = {}) => {
  let container = parent;
  if (shadowHost) {
    const host = document.createElement("div");
    host.id = `${id}-host`;
    parent.append(host);
    container = host.attachShadow({ mode: "open" });
  }
  const image = document.createElement("img");
  image.id = id;
  image.src = src;
  container.append(image);
  return image;
};
window.findElement = (id) => {
  const search = (root) => {
    const found = root.getElementById?.(id) ?? root.querySelector(`#${id}`);
    if (found) return found;
    for (const element of root.querySelectorAll("*")) {
      if (element.shadowRoot) {
        const nested = search(element.shadowRoot);
        if (nested) return nested;
      }
    }
    return null;
  };
  return search(document);
};
window.pixelOf = async (id) => {
  const element = window.findElement(id);
  const source = element instanceof HTMLImageElement
    ? element.src
    : element.style.backgroundImage.match(/url\\("?([^")]*)"?\\)/)?.[1] ?? "";
  if (!source.startsWith("data:")) return null;
  const image = new Image();
  image.src = source;
  await image.decode();
  const canvas = document.createElement("canvas");
  canvas.width = image.naturalWidth;
  canvas.height = image.naturalHeight;
  const context = canvas.getContext("2d");
  context.drawImage(image, 0, 0);
  const [red, green, blue] = context.getImageData(1, 1, 1, 1).data;
  return [red, green, blue];
};
window.setVariable = (element, name, value) => element.style.setProperty(name, value);
}"""


def png_bytes(*colors: tuple[int, int, int]) -> bytes:
    image = Image.new("RGBA", (8, 8), (*colors[0], 255))
    for index, color in enumerate(colors[1:], start=1):
        for row in range(8):
            image.putpixel((index, row), (*color, 255))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def static_files() -> dict[str, tuple[bytes, str]]:
    generic = png_bytes(GENERIC_ICON_RGB)
    return {
        "/": (PAGE_HTML.encode(), "text/html"),
        "/ha-themes.js": (render_support_module().encode(), "text/javascript"),
        GENERIC_ICON: (generic, "image/png"),
        OTHER_GENERIC_ICON: (generic, "image/png"),
        LOGO: (png_bytes(GENERIC_ICON_RGB, (255, 255, 255), (20, 20, 20)), "image/png"),
        REPLACEMENT_IMAGE: (png_bytes((128, 128, 128)), "image/png"),
        FONT_STYLESHEET: (b"", "text/css"),
    }


@pytest.fixture
def browser() -> Iterator[Browser]:
    with sync_playwright() as playwright:
        failures = []
        for options in ({"channel": "chrome"}, {}):
            try:
                launched = playwright.chromium.launch(**options)
            except PlaywrightError as error:
                failures.append(str(error).splitlines()[0])
                continue
            yield launched
            launched.close()
            return
        pytest.skip(f"no browser can launch (Google Chrome or Playwright Chromium): {failures}")


@pytest.fixture
def page_errors() -> list[str]:
    return []


@pytest.fixture
def page(browser: Browser, page_errors: list[str]) -> Iterator[Page]:
    files = static_files()

    def serve(route: Route) -> None:
        url = route.request.url
        for origin in (ORIGIN, CROSS_ORIGIN):
            if url.startswith(origin):
                path = url.removeprefix(origin).split("?")[0] or "/"
                if path in files:
                    body, content_type = files[path]
                    route.fulfill(body=body, content_type=content_type)
                    return
        route.abort()

    context = browser.new_context()
    context.route("**/*", serve)
    opened = context.new_page()
    opened.set_default_timeout(WAIT_SECONDS * 1000)
    opened.on("pageerror", lambda error: page_errors.append(str(error)))
    opened.goto(f"{ORIGIN}/")
    opened.evaluate(HELPERS)
    yield opened
    context.close()


def wait_for_color(page: Page, element_id: str, rgb: tuple[int, int, int]) -> None:
    deadline = time.monotonic() + WAIT_SECONDS
    while (pixel := page.evaluate("(id) => window.pixelOf(id)", element_id)) != list(rgb):
        assert time.monotonic() < deadline, f"{element_id} shows {pixel}, expected {list(rgb)}"
        page.wait_for_timeout(50)


def displayed_source(page: Page, element_id: str) -> str:
    return page.evaluate("(id) => window.findElement(id).src", element_id)


def set_root_color(page: Page, color: str) -> None:
    page.evaluate(
        "(color) => window.setVariable(document.documentElement, "
        "'--ha-themes-brand-icon-color', color)",
        color,
    )


def remove_root_variable(page: Page, name: str) -> None:
    page.evaluate("(name) => document.documentElement.style.removeProperty(name)", name)


def attach_shadow_is_native(page: Page) -> bool:
    return page.evaluate(
        "() => Element.prototype.attachShadow.toString().includes('[native code]')"
    )


def test_module_source_is_valid_javascript(tmp_path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    module = tmp_path / "ha-themes.mjs"
    module.write_text(SUPPORT_MODULE_SOURCE.read_text(encoding="utf-8"), encoding="utf-8")
    result = subprocess.run(
        [node, "--check", str(module)], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr


def test_module_stays_dormant_without_a_project_variable(
    page: Page, page_errors: list[str]
) -> None:
    page.evaluate(
        f"""() => {{
          window.addIcon("icon", "{GENERIC_ICON}", {{ shadowHost: true }});
          document.documentElement.style.setProperty("--primary-color", "red");
        }}"""
    )
    page.wait_for_timeout(SETTLE_MILLISECONDS)

    assert attach_shadow_is_native(page)
    assert displayed_source(page, "icon") == f"{ORIGIN}{GENERIC_ICON}"
    assert page.evaluate("() => document.querySelector('style[data-ha-themes]')") is None
    assert page_errors == []


def test_project_variable_activates_and_clearing_it_restores_the_original(
    page: Page, page_errors: list[str]
) -> None:
    page.evaluate(f"""() => window.addIcon("icon", "{GENERIC_ICON}", {{ shadowHost: true }})""")

    set_root_color(page, "rgb(255, 0, 0)")
    wait_for_color(page, "icon", RED)

    assert not attach_shadow_is_native(page)
    assert page.evaluate("() => !!document.querySelector('style[data-ha-themes]')")

    remove_root_variable(page, "--ha-themes-brand-icon-color")
    page.wait_for_function(f"() => window.findElement('icon').src === '{ORIGIN}{GENERIC_ICON}'")
    page.wait_for_function("() => !document.querySelector('style[data-ha-themes]')")
    assert page_errors == []


def test_only_generic_same_origin_icons_are_recolored(page: Page, page_errors: list[str]) -> None:
    set_root_color(page, "rgb(255, 0, 0)")
    page.evaluate(
        f"""() => {{
          window.addIcon("generic", "{GENERIC_ICON}", {{ shadowHost: true }});
          window.addIcon("logo", "{LOGO}", {{ shadowHost: true }});
          window.addIcon("cross", "{CROSS_ORIGIN}{GENERIC_ICON}", {{ shadowHost: true }});
          const background = document.createElement("div");
          background.id = "background";
          background.style.backgroundImage = 'url("{OTHER_GENERIC_ICON}")';
          document.body.append(background);
        }}"""
    )

    wait_for_color(page, "generic", RED)
    wait_for_color(page, "background", RED)
    page.wait_for_timeout(SETTLE_MILLISECONDS)
    assert displayed_source(page, "logo") == f"{ORIGIN}{LOGO}"
    assert displayed_source(page, "cross") == f"{CROSS_ORIGIN}{GENERIC_ICON}"

    page.evaluate("() => { window.findElement('cross').style.width = '12px'; }")
    page.wait_for_timeout(SETTLE_MILLISECONDS)
    assert displayed_source(page, "cross") == f"{CROSS_ORIGIN}{GENERIC_ICON}"
    assert page_errors == []


def test_a_source_replaced_by_the_frontend_is_not_forced_back(
    page: Page, page_errors: list[str]
) -> None:
    set_root_color(page, "rgb(255, 0, 0)")
    page.evaluate(
        f"""() => {{
          window.addIcon("replaced", "{GENERIC_ICON}", {{ shadowHost: true }});
          window.addIcon("sentinel", "{OTHER_GENERIC_ICON}", {{ shadowHost: true }});
        }}"""
    )
    wait_for_color(page, "replaced", RED)
    wait_for_color(page, "sentinel", RED)

    page.evaluate(f"() => {{ window.findElement('replaced').src = '{REPLACEMENT_IMAGE}'; }}")
    set_root_color(page, "rgb(0, 128, 0)")
    wait_for_color(page, "sentinel", GREEN)
    page.wait_for_timeout(SETTLE_MILLISECONDS)
    assert displayed_source(page, "replaced") == f"{ORIGIN}{REPLACEMENT_IMAGE}"

    page.evaluate(
        f"""() => {{
          const racing = window.addIcon("racing", "{GENERIC_ICON}", {{ shadowHost: true }});
          queueMicrotask(() => {{ racing.src = "{REPLACEMENT_IMAGE}"; }});
        }}"""
    )
    page.wait_for_timeout(SETTLE_MILLISECONDS)
    assert displayed_source(page, "racing") == f"{ORIGIN}{REPLACEMENT_IMAGE}"
    assert page_errors == []


def test_each_themed_subtree_uses_its_own_color(page: Page, page_errors: list[str]) -> None:
    set_root_color(page, "rgb(255, 0, 0)")
    page.evaluate(
        f"""() => {{
          for (const [id, color] of [["global", ""], ["card", "rgb(0, 0, 255)"]]) {{
            const card = document.createElement("div");
            card.id = `${{id}}-card`;
            if (color) card.style.setProperty("--ha-themes-brand-icon-color", color);
            document.body.append(card);
            window.addIcon(id, "{GENERIC_ICON}", {{ parent: card, shadowHost: true }});
          }}
        }}"""
    )
    wait_for_color(page, "global", RED)
    wait_for_color(page, "card", BLUE)

    page.evaluate(
        "() => window.findElement('card-card').style"
        ".setProperty('--ha-themes-brand-icon-color', 'rgb(0, 128, 0)')"
    )
    wait_for_color(page, "card", GREEN)
    assert page.evaluate("() => window.pixelOf('global')") == list(RED)

    page.evaluate(
        "() => window.findElement('card-card').style.removeProperty('--ha-themes-brand-icon-color')"
    )
    wait_for_color(page, "card", RED)
    assert page_errors == []


def test_body_takes_the_theme_font_and_its_size_adjustment(
    page: Page, page_errors: list[str]
) -> None:
    body_font = (
        "() => { const style = getComputedStyle(document.body); "
        "return [style.fontFamily, style.fontSizeAdjust]; }"
    )
    page.evaluate(
        """() => {
          document.documentElement.style.setProperty("--ha-font-family-body", "Arial");
          document.documentElement.style.setProperty("--ha-themes-font-size-adjust", "0.5");
        }"""
    )
    set_root_color(page, "rgb(255, 0, 0)")
    page.wait_for_function(f"() => ({body_font})()[0] === 'Arial'")
    assert page.evaluate(body_font) == ["Arial", "0.5"]

    remove_root_variable(page, "--ha-themes-font-size-adjust")
    assert page.evaluate(body_font) == ["Arial", "none"]
    assert page_errors == []


def test_font_stylesheet_follows_the_theme_variable(page: Page, page_errors: list[str]) -> None:
    links = "() => [...document.head.querySelectorAll('link[data-ha-themes-font-stylesheet]')]"
    page.evaluate(
        "(href) => window.setVariable(document.documentElement, "
        "'--ha-themes-font-stylesheet', `\"${href}\"`)",
        FONT_STYLESHEET,
    )
    page.wait_for_function(f"() => ({links})().length === 1")
    assert page.evaluate(f"() => ({links})()[0].getAttribute('href')") == FONT_STYLESHEET
    assert page.evaluate(f"() => ({links})()[0].rel") == "stylesheet"

    remove_root_variable(page, "--ha-themes-font-stylesheet")
    page.wait_for_function(f"() => ({links})().length === 0")
    assert page_errors == []


def test_only_the_dashboard_header_paints_the_translucent_header_background(
    page: Page, page_errors: list[str]
) -> None:
    header_background = """(tag) => {
      const header = window.findElement(`${tag}-header`);
      return getComputedStyle(header).backgroundColor;
    }"""
    page.evaluate(
        """() => {
          const root = document.documentElement.style;
          root.setProperty("--app-header-background-color", "rgb(0, 0, 255)");
          root.setProperty("--ha-themes-dashboard-header-background", "rgba(255, 0, 0, 0.5)");
          for (const tag of ["hui-root", "ha-header-bar"]) {
            const host = document.createElement(tag);
            const shadow = host.attachShadow({ mode: "open" });
            const sheet = new CSSStyleSheet();
            sheet.replaceSync(".header { background-color: var(--app-header-background-color); }");
            shadow.adoptedStyleSheets = [sheet];
            const header = document.createElement("div");
            header.id = `${tag}-header`;
            header.className = "header";
            shadow.append(header);
            document.body.append(host);
          }
        }"""
    )
    page.wait_for_function(f"() => ({header_background})('hui-root') === 'rgba(255, 0, 0, 0.5)'")
    assert page.evaluate(header_background, "ha-header-bar") == "rgb(0, 0, 255)"

    remove_root_variable(page, "--ha-themes-dashboard-header-background")
    page.wait_for_function(f"() => ({header_background})('hui-root') === 'rgb(0, 0, 255)'")
    assert page_errors == []


def test_dropdown_menus_take_the_theme_menu_background(page: Page, page_errors: list[str]) -> None:
    menu_background = "() => getComputedStyle(window.findElement('menu')).backgroundColor"
    page.evaluate(
        """() => {
          const root = document.documentElement.style;
          root.setProperty("--card-background-color", "rgb(0, 0, 255)");
          root.setProperty("--ha-themes-menu-background", "rgb(255, 0, 0)");
          const host = document.createElement("ha-dropdown");
          const shadow = host.attachShadow({ mode: "open" });
          const sheet = new CSSStyleSheet();
          sheet.replaceSync(
            ":host { --wa-color-surface-raised: var(--card-background-color); }"
            + " #menu { background-color: var(--wa-color-surface-raised); }"
          );
          shadow.adoptedStyleSheets = [sheet];
          const menu = document.createElement("div");
          menu.id = "menu";
          shadow.append(menu);
          document.body.append(host);
        }"""
    )
    page.wait_for_function(f"() => ({menu_background})() === 'rgb(255, 0, 0)'")

    remove_root_variable(page, "--ha-themes-menu-background")
    page.wait_for_function(f"() => ({menu_background})() === 'rgb(0, 0, 255)'")
    assert page_errors == []


def test_toasts_take_the_theme_edge(page: Page, page_errors: list[str]) -> None:
    toast_shadow = "() => getComputedStyle(window.findElement('toast')).boxShadow"
    page.evaluate(
        """() => {
          const root = document.documentElement.style;
          root.setProperty("--wa-shadow-l", "rgb(0, 0, 255) 0px 16px 32px 0px");
          root.setProperty("--ha-themes-toast-box-shadow", "rgb(255, 0, 0) 0px 0px 0px 1px");
          const host = document.createElement("ha-toast");
          const shadow = host.attachShadow({ mode: "open" });
          const sheet = new CSSStyleSheet();
          sheet.replaceSync(".toast { box-shadow: var(--wa-shadow-l); }");
          shadow.adoptedStyleSheets = [sheet];
          const toast = document.createElement("div");
          toast.id = "toast";
          toast.className = "toast";
          shadow.append(toast);
          document.body.append(host);
        }"""
    )
    page.wait_for_function(f"() => ({toast_shadow})() === 'rgb(255, 0, 0) 0px 0px 0px 1px'")

    remove_root_variable(page, "--ha-themes-toast-box-shadow")
    page.wait_for_function(f"() => ({toast_shadow})() === 'rgb(0, 0, 255) 0px 16px 32px 0px'")
    assert page_errors == []


def test_input_chips_take_the_theme_corner_radius(page: Page, page_errors: list[str]) -> None:
    chip_radius = "() => getComputedStyle(window.findElement('chip')).borderTopLeftRadius"
    page.evaluate(
        """() => {
          document.documentElement.style.setProperty("--ha-themes-corner-radius", "8px");
          const host = document.createElement("ha-input-chip");
          const shadow = host.attachShadow({ mode: "open" });
          const sheet = new CSSStyleSheet();
          sheet.replaceSync(
            ":host { --ha-button-border-radius: 16px; }"
            + " #chip { border-radius: var(--ha-button-border-radius); }"
          );
          shadow.adoptedStyleSheets = [sheet];
          const chip = document.createElement("div");
          chip.id = "chip";
          shadow.append(chip);
          document.body.append(host);
        }"""
    )
    page.wait_for_function(f"() => ({chip_radius})() === '8px'")

    remove_root_variable(page, "--ha-themes-corner-radius")
    page.wait_for_function(f"() => ({chip_radius})() === '16px'")
    assert page_errors == []


def test_map_overview_panel_takes_the_theme_menu_background(
    page: Page, page_errors: list[str]
) -> None:
    panel_backgrounds = """() => ['panel', 'pill', 'outside'].map(
      (id) => getComputedStyle(window.findElement(id)).backgroundColor
    )"""
    page.evaluate(
        """() => {
          const root = document.documentElement.style;
          root.setProperty("--card-background-color", "rgb(0, 0, 255)");
          root.setProperty("--ha-themes-menu-background", "rgb(255, 0, 0)");
          const host = document.createElement("hui-map-overview");
          const shadow = host.attachShadow({ mode: "open" });
          const sheet = new CSSStyleSheet();
          sheet.replaceSync(
            ".panel, .pill, #outside { background-color: var(--card-background-color); }"
          );
          shadow.adoptedStyleSheets = [sheet];
          const panel = document.createElement("div");
          panel.id = "panel";
          panel.className = "panel";
          const pill = document.createElement("span");
          pill.id = "pill";
          pill.className = "pill";
          panel.append(pill);
          const outside = document.createElement("div");
          outside.id = "outside";
          shadow.append(panel, outside);
          document.body.append(host);
        }"""
    )
    page.wait_for_function(
        f"() => ({panel_backgrounds})().join() === 'rgb(255, 0, 0),rgb(255, 0, 0),rgb(0, 0, 255)'"
    )

    remove_root_variable(page, "--ha-themes-menu-background")
    page.wait_for_function(
        f"() => ({panel_backgrounds})().every((color) => color === 'rgb(0, 0, 255)')"
    )
    assert page_errors == []


def test_map_labels_take_the_theme_font(page: Page, page_errors: list[str]) -> None:
    label_fonts = """() => ['map-marker', 'other-marker'].map(
      (id) => getComputedStyle(window.findElement(id)).fontFamily
    )"""
    page.evaluate(
        """() => {
          document.documentElement.style.setProperty("--ha-font-family-body", "serif");
          const mapSheet = new CSSStyleSheet();
          mapSheet.replaceSync(".maplibregl-map { font-family: monospace; }");
          for (const [hostName, markerId] of [
            ["ha-map", "map-marker"],
            ["ha-other-map", "other-marker"],
          ]) {
            const host = document.createElement(hostName);
            const shadow = host.attachShadow({ mode: "open" });
            shadow.adoptedStyleSheets = [mapSheet];
            const map = document.createElement("div");
            map.className = "maplibregl-map";
            const marker = document.createElement("div");
            marker.id = markerId;
            map.append(marker);
            shadow.append(map);
            document.body.append(host);
          }
        }"""
    )
    page.wait_for_timeout(SETTLE_MILLISECONDS)
    assert page.evaluate(label_fonts) == ["monospace", "monospace"]

    set_root_color(page, "rgb(255, 0, 0)")
    page.wait_for_function(f"() => ({label_fonts})().join() === 'serif,monospace'")
    assert page_errors == []


def test_integration_entry_lists_take_the_card_tone(page: Page, page_errors: list[str]) -> None:
    list_backgrounds = """() => ['entry-list', 'page-list'].map(
      (id) => getComputedStyle(window.findElement(id)).backgroundColor
    )"""
    set_root_color(page, "rgb(255, 0, 0)")
    page.evaluate(
        """() => {
          const root = document.documentElement.style;
          root.setProperty("--card-background-color", "rgb(0, 0, 255)");
          root.setProperty("--ha-card-background", "rgb(0, 255, 0)");
          const listSheet = new CSSStyleSheet();
          listSheet.replaceSync(`
            .config-entry-wrapper { background-color: var(--card-background-color); }
          `);
          for (const [hostName, listId] of [
            ["ha-config-entry-row", "entry-list"],
            ["ha-config-integration-page", "page-list"],
          ]) {
            const host = document.createElement(hostName);
            const shadow = host.attachShadow({ mode: "open" });
            shadow.adoptedStyleSheets = [listSheet];
            const wrapper = document.createElement("div");
            wrapper.id = listId;
            wrapper.className = "config-entry-wrapper";
            shadow.append(wrapper);
            document.body.append(host);
          }
        }"""
    )
    page.wait_for_function(
        f"() => ({list_backgrounds})().join() === 'rgb(0, 255, 0),rgb(0, 0, 255)'"
    )
    assert page_errors == []


def test_icon_tiles_take_the_entity_color_of_their_hue(page: Page, page_errors: list[str]) -> None:
    tile_backgrounds = """() => ['property-tile', 'attribute-tile', 'unknown-tile'].map(
      (id) => getComputedStyle(window.findElement(id)).backgroundColor
    )"""
    set_root_color(page, "rgb(255, 0, 0)")
    page.evaluate(
        """() => {
          const root = document.documentElement.style;
          root.setProperty("--indigo-color", "#4d5ea2");
          root.setProperty("--amber-color", "#eec876");
          root.setProperty("--ha-themes-icon-tile-palette-share", "100%");
          root.setProperty("--ha-themes-icon-tile-max-lightness", "0.6");
          const navigation = document.createElement("ha-config-navigation-list");
          const navigationShadow = navigation.attachShadow({ mode: "open" });
          const propertyTile = document.createElement("div");
          propertyTile.id = "property-tile";
          propertyTile.style = "background-color: #0D47A1";
          const unknownTile = document.createElement("div");
          unknownTile.id = "unknown-tile";
          unknownTile.style = "background-color: #123456";
          navigationShadow.append(propertyTile, unknownTile);
          const info = document.createElement("ha-config-info");
          const infoShadow = info.attachShadow({ mode: "open" });
          const attributeTile = document.createElement("div");
          attributeTile.id = "attribute-tile";
          attributeTile.setAttribute("style", "background-color: #F1C447;;");
          infoShadow.append(attributeTile);
          document.body.append(navigation, info);
        }"""
    )
    page.wait_for_function(f"() => ({tile_backgrounds})()[0].startsWith('oklch')")
    property_tile, attribute_tile, unknown_tile = page.evaluate(tile_backgrounds)
    assert property_tile.startswith("oklch(0.5")
    assert attribute_tile.startswith("oklch(0.6 ")
    assert unknown_tile == "rgb(18, 52, 86)"

    for name in ("--ha-themes-icon-tile-palette-share", "--ha-themes-icon-tile-max-lightness"):
        remove_root_variable(page, name)
    stock = page.evaluate(
        """() => ['property-tile', 'attribute-tile'].map((id) => {
          const context = document.createElement("canvas").getContext("2d");
          context.fillStyle = getComputedStyle(window.findElement(id)).backgroundColor;
          context.fillRect(0, 0, 1, 1);
          return [...context.getImageData(0, 0, 1, 1).data.slice(0, 3)];
        })"""
    )
    assert stock == [[13, 71, 161], [241, 196, 71]]
    assert page_errors == []


STOCK_FILL = "200 200 200 255"
STOCK_HOVER_FILL = "150 150 150 255"
CLEAR_FILL = "0 0 0 0"

FIELD_VARIABLES = {
    "--ha-themes-field-outline": "1",
    "--ha-themes-field-border-color": "rgb(255, 0, 0)",
    "--ha-themes-field-border-radius": "8px",
}

ADD_FIELDS = """() => {
  const root = document.documentElement.style;
  root.setProperty("--primary-color", "rgb(0, 0, 255)");
  root.setProperty("--ha-color-border-danger-normal", "rgb(0, 128, 0)");
  root.setProperty("--ha-border-radius-sm", "4px");
  root.setProperty("--ha-border-radius-square", "0px");
  root.setProperty("--ha-color-form-background", "rgb(200, 200, 200)");
  root.setProperty("--ha-color-form-background-hover", "rgb(150, 150, 150)");
  root.setProperty("--ha-color-border-neutral-normal", "rgb(255, 165, 0)");
  root.setProperty("--secondary-text-color", "rgb(100, 100, 100)");
  const stockSheet = (css) => {
    const sheet = new CSSStyleSheet();
    sheet.replaceSync(css);
    return sheet;
  };
  const addControl = (hostName, controlName, id, hostCss) => {
    const host = document.createElement(hostName);
    host.id = `${id}-host`;
    const shadow = host.attachShadow({ mode: "open" });
    shadow.adoptedStyleSheets = [stockSheet(hostCss)];
    const control = document.createElement(controlName);
    control.className = "input";
    const controlShadow = control.attachShadow({ mode: "open" });
    const base = document.createElement("div");
    base.id = id;
    base.part = "base";
    const field = document.createElement("input");
    field.id = `${id}-field`;
    base.append(field);
    controlShadow.append(base);
    shadow.append(control);
    document.body.append(host);
    return host;
  };
  const sharedCss = `.input::part(base) {
    background-color: var(--ha-color-form-background); border: none; border-radius: 4px 4px 0 0;
  }`;
  addControl("ha-input", "wa-input", "input", `${sharedCss}
    :host([appearance=material]) ::part(base)::after { content: ""; display: block; height: 1px; }
    wa-input::part(base):hover { background-color: var(--ha-color-form-background-hover); }`
  ).setAttribute("appearance", "material");
  addControl("ha-textarea", "wa-textarea", "textarea", `${sharedCss}
    wa-textarea::part(base)::after { content: ""; display: block; height: 1px; }
    wa-textarea:hover::part(base) { background-color: var(--ha-color-form-background-hover); }`);
  const picker = document.createElement("ha-picker-field");
  const pickerShadow = picker.attachShadow({ mode: "open" });
  pickerShadow.adoptedStyleSheets = [stockSheet(`
    .field {
      display: flex; height: 20px; background-color: var(--ha-color-form-background);
      border-radius: 4px; border-end-start-radius: 0; border-end-end-radius: 0;
    }
    .field:hover { background-color: var(--ha-color-form-background-hover); }
    .field::after { content: ""; display: block; height: 1px; }`)];
  const pickerField = document.createElement("div");
  pickerField.id = "picker";
  pickerField.className = "field";
  const trigger = document.createElement("button");
  trigger.id = "picker-trigger";
  trigger.append(document.createElement("ha-combo-box-item"));
  pickerField.append(trigger);
  pickerShadow.append(pickerField);
  document.body.append(picker);
}"""

FIELD_STYLES = """(id) => {
  const element = window.findElement(id);
  const style = getComputedStyle(element);
  const rgba = (color) => {
    const context = new OffscreenCanvas(1, 1).getContext("2d");
    context.fillStyle = color || "transparent";
    context.fillRect(0, 0, 1, 1);
    return Array.from(context.getImageData(0, 0, 1, 1).data).join(" ");
  };
  return {
    fill: rgba(style.backgroundColor),
    ripple: rgba(style.getPropertyValue("--ha-ripple-hover-color")),
    width: style.borderTopWidth,
    color: style.borderTopColor,
    radius: `${style.borderTopLeftRadius} ${style.borderBottomLeftRadius}`,
    underline: getComputedStyle(element, "::after").opacity,
  };
}"""


def field_styles(page: Page, element_id: str) -> dict[str, str]:
    return page.evaluate(FIELD_STYLES, element_id)


def set_field_variables(page: Page) -> None:
    for name, value in FIELD_VARIABLES.items():
        page.evaluate(
            "([name, value]) => window.setVariable(document.documentElement, name, value)",
            [name, value],
        )


@pytest.mark.parametrize("element_id", ["input", "textarea", "picker"])
def test_form_fields_keep_their_underline_without_the_field_variables(
    page: Page, page_errors: list[str], element_id: str
) -> None:
    set_root_color(page, "rgb(255, 0, 0)")
    page.evaluate(ADD_FIELDS)
    page.wait_for_function(
        "() => window.findElement('input-host').shadowRoot.adoptedStyleSheets.length === 2"
    )

    styles = field_styles(page, element_id)
    assert styles["width"] == "0px"
    assert styles["underline"] == "1"
    assert styles["radius"] == "4px 0px"
    assert styles["fill"] == STOCK_FILL
    assert field_styles(page, "picker")["ripple"] == "100 100 100 255"
    page.locator(f"#{element_id}").hover()
    assert field_styles(page, element_id)["fill"] == STOCK_HOVER_FILL
    assert page_errors == []


@pytest.mark.parametrize("element_id", ["input", "textarea", "picker"])
def test_form_fields_take_an_outline_instead_of_the_underline(
    page: Page, page_errors: list[str], element_id: str
) -> None:
    set_root_color(page, "rgb(255, 0, 0)")
    set_field_variables(page)
    page.evaluate(ADD_FIELDS)
    page.wait_for_function(f"() => ({FIELD_STYLES})('{element_id}').width === '1px'")

    assert field_styles(page, element_id) == {
        "fill": CLEAR_FILL,
        "ripple": CLEAR_FILL,
        "width": "1px",
        "color": "rgb(255, 0, 0)",
        "radius": "8px 8px",
        "underline": "0",
    }

    remove_root_variable(page, "--ha-themes-field-outline")
    page.wait_for_function(f"() => ({FIELD_STYLES})('{element_id}').underline === '1'")
    assert field_styles(page, element_id)["width"] == "0px"
    assert field_styles(page, element_id)["fill"] == STOCK_FILL
    assert page_errors == []


@pytest.mark.parametrize("element_id", ["input", "textarea", "picker"])
def test_outlined_fields_stay_clear_and_step_their_outline_on_hover(
    page: Page, page_errors: list[str], element_id: str
) -> None:
    set_root_color(page, "rgb(255, 0, 0)")
    set_field_variables(page)
    page.evaluate(ADD_FIELDS)
    page.wait_for_function(f"() => ({FIELD_STYLES})('{element_id}').width === '1px'")

    page.locator(f"#{element_id}").hover()
    styles = field_styles(page, element_id)
    assert styles["fill"] == CLEAR_FILL
    assert styles["color"] == "rgb(255, 165, 0)"
    assert page_errors == []


def test_outlined_fields_show_focus_and_errors_in_the_outline(
    page: Page, page_errors: list[str]
) -> None:
    set_root_color(page, "rgb(255, 0, 0)")
    set_field_variables(page)
    page.evaluate(ADD_FIELDS)
    page.wait_for_function(f"() => ({FIELD_STYLES})('input').width === '1px'")

    page.evaluate("() => window.findElement('input-field').focus()")
    assert field_styles(page, "input")["color"] == "rgb(0, 0, 255)"
    page.evaluate(
        "() => window.findElement('input-host').shadowRoot.querySelector('wa-input')"
        ".classList.add('invalid')"
    )
    assert field_styles(page, "input")["color"] == "rgb(0, 128, 0)"

    page.evaluate("() => window.findElement('picker-trigger').focus()")
    assert field_styles(page, "picker")["color"] == "rgb(0, 0, 255)"
    page.evaluate(
        "() => window.findElement('picker').getRootNode().host.setAttribute('invalid', '')"
    )
    assert field_styles(page, "picker")["color"] == "rgb(0, 128, 0)"
    assert page_errors == []
