# How Home Assistant themes work today

Verified against frontend `20261028.4` / Core `2026.11.0`, by reading the shipped theme
sources and observing the running frontend in Google Chrome. Much of the theming advice
online predates the 2025–2026 design-token rework; this page describes what the current
frontend actually does.

## The token layers

The frontend declares its defaults as CSS custom properties on `html`, in layers that
build on each other through `var()`:

```text
core palette      --ha-color-primary-40: #009ac7            (raw tonal scales)
      │
semantic colors   --ha-color-fill-primary-loud-resting: var(--ha-color-primary-40)
      │
bridges           --wa-color-brand-fill-loud: var(--ha-color-fill-primary-loud-resting)
                  --mdc-theme-primary: var(--primary-color)
      │
components        ha-button, ha-card, dialogs, tiles …
```

| Layer | Prefix | What it is |
| --- | --- | --- |
| Core palette | `ha-color-{primary,neutral,red,orange,green}-{05…95}`, `ha-color-black/white` | Eleven-step tonal scales. Everything semantic derives from them. |
| Semantic colors | `ha-color-{text,border,fill,on,surface,form}-*` | Role colors in three intensities (`quiet`, `normal`, `loud`) and states (`resting`, `hover`, `active`). |
| Foundation | `ha-space-*`, `ha-border-{width,radius}-*`, `ha-box-shadow-*`, `ha-animation-duration-*` | Spacing (4px grid), radii, elevation and motion. Motion collapses to `1ms` under `prefers-reduced-motion`. |
| Typography | `ha-font-{family,size,weight}-*`, `ha-line-height-*` | Families, a size scale multiplied by `ha-font-size-scale`, weights. `ha-font-family-longform` is declared but not read by any component. |
| Application colors | `primary-color`, `card-background-color`, `sidebar-*`, `input-*` … | The classic theme variables. Many are **hard-coded hex values per mode**, not derived. |
| State colors | `state-<domain>-<state>-color` | Entity colors, mostly pointing at the named colors (`--amber-color`, …). |
| Data visualization | `color-1…54`, `energy-*`, `history-*` | Chart, energy dashboard and history colors. |
| Web Awesome bridge | `wa-*` | Maps HA tokens onto the Web Awesome components the frontend now uses for buttons, dialogs, inputs and tooltips. |
| Material bridge | `mdc-*`, `md-*` | Maps HA tokens onto the remaining Material components. |
| Component hooks | `ha-card-*`, `ha-dialog-*`, `ha-tile-*` … | Read by components with a fallback but never declared — set them to customise one component. |

Full lists with defaults: [tokens-global.md](tokens-global.md) and
[tokens-components.md](tokens-components.md).

## How a theme is applied

Themes are defined in YAML (`frontend: themes:`) and applied by
`applyThemesOnElement` in the frontend. For a custom theme it:

1. **In dark mode, starts from the built-in dark defaults** (dark semantic and
   application colors).
2. Merges the theme's **base keys** on top.
3. Merges `modes.light` or `modes.dark` on top of that.
4. Re-applies every **derived** default (any token whose value contains `var()`) together
   with the theme's keys, as inline styles on the themed element.
5. For every key whose value is a **hex color**, also sets `--rgb-<key>` (`"r,g,b"`), unless
   the theme sets that `rgb-` key itself.

Consequences for theme authors:

- **Anything that differs between light and dark must live under `modes`.** A base key is
  applied after the dark defaults, so it wins in both modes.
- **Without a `modes` section, the theme has no dark mode** and the profile's dark-mode
  toggle has no effect on it.
- **Override the core palette and the semantic layer follows** — in both modes, because the
  dark semantic defaults reference the same palette steps. This is the highest-leverage
  part of a theme.
- **Hard-coded application colors do not follow the palette.** `primary-background-color`,
  `card-background-color`, `secondary-background-color`, `primary-text-color`,
  `divider-color`, the `input-*` colors and others must be set per mode.
- **Use hex for colors** so the `rgb-` companions are generated; several components read
  `rgba(var(--rgb-primary-text-color), 0.6)`-style values. A `var()` or `rgba()` value gets
  no companion.
- **`primary-color` and the text colors are derived** (`var(--ha-color-primary-40)`,
  `var(--ha-color-text-primary)`), so they follow the palette — but their `rgb-` companions
  stay at the stock values. Setting them explicitly as hex keeps both in agreement.

## Selecting a theme

The selected theme and dark-mode preference are stored per user on the server (frontend
user data) and restored after the app boots; `localStorage.selectedTheme` is only a cache
for the loading screen. Automations can still set the default theme with
`frontend.set_theme`, and `frontend.reload_themes` reloads YAML changes without a restart.

## Fonts

Setting `ha-font-family-body` is not enough to change the font everywhere:

- **The page body hard-codes Roboto.** `index.html` declares
  `body { font-family: Roboto, Noto, sans-serif }` as a literal baked in at build time, so
  everything that inherits from the body — sidebar, header, banners, buttons — ignores the
  theme. Dashboards and settings cards read the variable and do follow it.
- **Material components fall back to a literal Roboto.** They read
  `mdc-typography-font-family`, which the frontend never sets.
- **The map sets its own font.** MapLibre's stylesheet sets Helvetica Neue on the map, so
  the entity markers and the attribution inherit it instead of the theme font.
- **Charts draw their text with a literal Roboto.** `ha-chart-base` registers an ECharts
  theme whose `textStyle.fontFamily` is `Roboto, Noto, sans-serif`, and ECharts draws axis
  labels and legends on a canvas, which no CSS reaches; the tooltip copies the same font.
- **The code editor sets Roboto on two selectors.** CodeMirror's theme gives the completion
  details (the friendly name next to an entity id) and the search panel fields a literal
  Roboto.
- **Themes cannot load web fonts**, since they only set CSS variables.

The builder sets that Material token to `var(--ha-font-family-body)` in every theme, and
generates one support module, which the integration loads on every page, that binds
`body` to `var(--ha-font-family-body)` while a project theme is the global theme, points the
map, the completion details and the search fields of the code editor at the same font, and loads
web fonts on demand. For the charts it wraps `ha-chart-base`'s `_createTheme`, which builds the
ECharts theme from the chart element's computed style when the chart is set up: when that style
carries a project theme (`ha-themes-brand-icon-color` resolves there, from the global, view or
card theme), the stack is replaced by the `ha-font-family-body` it resolves, and any other chart
keeps the stock stack. `toolkit/tests/test_upstream_fonts.py` fails when the installed frontend
changes either literal or renames the method, so the wrap is reviewed instead of silently
missing. A theme that declares
`typography.stylesheet` carries its URL in the project variable `ha-themes-font-stylesheet`;
the module adds the stylesheet while that variable is set on the page (by the global theme) or
on a view or card (by a view or card theme), and removes it as soon as no visible theme sets it,
so switching themes needs no reload. With a theme that declares no stylesheet, such as the
shipped Anthropic theme, the default theme or any other theme, the module requests no web font. With both in place, an audit of every rendered text node in Chrome
finds only the theme font. Fonts declared on the document are visible inside every shadow
root.

The chart wrap is installed once `ha-chart-base` is defined and changes nothing for a chart
outside a project theme. Apart from it, the module is dormant while no project theme is in use:
it only notices when a theme sets a
`ha-themes-*` variable (every project theme sets `ha-themes-brand-icon-color`), without
patching `attachShadow` or observing any shadow root. The first such variable, from the
global theme or from a view or card theme, activates it; it then scans the shadow roots that
already exist and watches new ones. Once no element declares a project variable any more, it
restores the icons, removes the font stylesheets, disconnects its observers and goes dormant
again.

### Wide fonts

A theme font is rarely as narrow as Roboto, and the frontend sizes its labels, tiles and
table columns for Roboto. Poppins sets the same text about 21 % wider, so labels that fit
in the default theme can end in an ellipsis. `typography.size_adjust` compensates: it is
carried in `ha-themes-font-size-adjust`, and the body binding applies it as
`font-size-adjust`, which every element inherits, shadow roots included. The font is then
scaled so that its x-height is that ratio of the font size. For Poppins, `0.528`, the
x-height of Roboto, makes lowercase text exactly as tall as in the default theme (Poppins is
drawn at about 96 % of its natural size) and leaves line heights unchanged.
Like the body font, it applies while a project theme is the global theme, not under a view
or card theme.

`ha-font-size-scale` and letter-spacing are weaker tools for this. Many labels use literal
`rem` or `px` sizes that ignore the scale, and Material components set their own
letter-spacing, so neither reaches the data tables. Measured over `/lovelace/0`, `/theme-lab/components`,
`/config/entities` and `/config/dashboard` at 1400 px and 390 px wide, the default theme
truncates 18 labels and Poppins without adjustment 23. A scale of 0.95 brings that to 21,
a body letter-spacing of -0.02em to 21, and `size_adjust: "0.528"` to 20, without making
lowercase text any smaller than in the default theme. Two labels stay cut at 390 px: a
description in the settings list, and "4 updates available" on the overview, which stays
cut even with Poppins drawn at 92 % of its size, below which text gets too small. The platform's UI font, which the shipped Anthropic theme
uses, truncates exactly what the default theme does.

## Entity and chart colors

- **Entity colors resolve through a chain.** For each stateful domain the frontend tries
  `--state-<domain>-<device_class>-<state>-color`, then `--state-<domain>-<state>-color`,
  `--state-<domain>-<active|inactive>-color` and `--state-<active|inactive>-color`. The
  declared defaults point at the named colors (`--amber-color`, `--green-color`, …), so
  restyling the named colors re-tints every entity at once.
- **Named colors have no dark variants.** The stock palette uses the same values in both
  modes, so `--indigo-color` and `--deep-purple-color` reach only about 2.5:1 on the dark
  card surface, under the 3:1 expected of icons.
- **Charts read colors in JavaScript.** `--graph-color-N` is tried first and is unset by
  default; `--color-N` (1–54, cycled) is the fallback and is also used by calendars and
  maps. The values are parsed as colors in script, so use hex.
- **The stock chart series are well separated but not mode-aware.** Measured with the
  categorical checks, the eight default series keep adjacent color-vision-deficiency
  separation at ΔE 10.8 and normal-vision separation at 18.0, but three sit above the
  light-mode lightness band, three are below the chroma floor, five are under 3:1 on a
  white card, and the same values are used in dark mode. Pushing them into a band without
  re-ordering collapses their separation, which is why the builder leaves them alone
  unless a theme declares its own series.

## Integration icons

Integration and media-source icons are PNGs served by `/api/brands/integration/<domain>/`,
which proxies and caches the brands CDN. Core integrations without a logo of their own
(camera, image, TTS, backup, sun, shopping list, AI task, media source…) use a generic icon
drawn in a single flat `#00abf8`; theme variables cannot reach a bitmap, and the endpoint
only accepts local overrides for custom integrations.

The support module recolors them in the browser: while active, it watches every shadow root for
`/api/brands/` images, loads each one into a canvas, and recolors it only when every opaque
pixel is that exact blue, so real logos — multicolored or monochrome in another color — are
never touched. The color comes from `--ha-themes-brand-icon-color`; a theme that does not
set it (the default theme included) gets the original images back.

## Settings icon tiles

Settings, System, About and the search dialog draw each entry's icon on a colored tile whose
color is a literal in the frontend code (`#0D47A1`, `#F1C447`, `#B1345C`…), written inline,
so no theme variable reaches it. On a warm theme these saturated, mostly cool tiles are the
only shapes off the palette, and the white glyph on the yellow one is about 1.6:1.

The support module adopts a stylesheet into the components that draw them (the settings
navigation list, About, and the list of the search dialog) that matches each known
literal by value and replaces it with the entity color of the same hue (`#0D47A1` takes
`--indigo-color`, `#F1C447` `--amber-color`), so the tiles stay as distinct from one another as
in stock Home Assistant while following the theme's entity palette. Every project theme sets
`ha-themes-icon-tile-palette-share` (`100%`) and `ha-themes-icon-tile-max-lightness` (`0.6`,
in OKLCH), which caps the tile so the white glyph keeps about 4:1 in both modes. Without
those variables the rules reproduce the literal, so other themes see the stock tiles. A
literal the table does not know keeps its stock color; `toolkit/tests/test_icon_tiles.py`
fails when the installed frontend uses one. The Home Assistant and Open Home Foundation logos
on About are brand marks and are left alone.

The tiles are drawn round with `ha-border-radius-circle`, which a theme keeps round for
avatars and round buttons, so the same components (and the restart dialog) also give the
tiles `ha-themes-corner-radius`: they turn into the theme's rounded squares, like the entity
tile icons. The search dialog sets the circle inline next to the tile color, so its rule
matches a start-slot element whose inline style holds both, and an inline circle without a
color stays round. Without `ha-themes-corner-radius` (`corner_radius: false`) the tiles keep
their circle.

## Form fields

Text inputs (`ha-input`), text areas (`ha-textarea`), selects and pickers (`ha-picker-field`,
which `ha-select`, `ha-generic-picker` and the entity, area and other pickers render) draw a
filled box with a bottom line from an `::after` rule inside their shadow roots, and that line is
their only edge, focus and error indicator. The labels field (`ha-labels-picker`) and the time
input (`ha-base-time-input`, one input per unit joined into a strip) draw the same line as a
border. No theme variable reaches any of it.

The support module adopts a stylesheet into those components that outlines the field, hides
the line and clears the fill while a theme sets the switch `ha-themes-field-outline` to `1`.
The outline takes `ha-themes-field-border-color` and `ha-themes-field-border-radius` (the
builder sets `ha-color-border-neutral-quiet` and `ha-border-radius-md`, which the
[corner radius](#corner-radius) sets), steps to
`ha-color-border-neutral-normal` on hover, turns `primary-color` on focus and
`ha-color-border-danger-normal` on an invalid value, and fades to half on a disabled input or
text area; disabled selects already dim as a whole. The time input outlines the whole strip
instead of each unit.

The fields paint their resting, hover and disabled fills from `ha-color-form-background`,
`-hover` and `-disabled` (the labels field from `mdc-text-field-fill-color`), and selects tint
on hover with their ripple. Checkboxes share the hover fill, so the themes keep the tokens and
the stylesheet clears them only inside the fields: the host keeps the inherited value and the
field element redefines the token from it, mixed with `transparent` by the switch. Every state
then shows the page, card or dialog behind the field, and field text sits on the same
`background` and `surface` the contrast checks measure it against. Fields in the `outlined` appearance (the search fields) keep their own
outline. Without the switch every rule resolves to the stock look, so other themes are
unaffected; a theme opts out with `field_outline: false`.

## Corner radius

The frontend rounds by size: `ha-border-radius-sm` (4px) for small controls up to `-6xl`
(36px) for large ones, and `ha-border-radius-pill` (9999px) for buttons, badges, tile icons and
progress bars. Many components read a hook or a library variable first (`ha-card-border-radius`,
`ha-dialog-border-radius`, `ha-button-border-radius`, `wa-panel-border-radius`,
`mdc-shape-small` …) whose fallback is a literal or a fixed step,
so the scale alone does not reach them.

A theme's `corner_radius` (default `8px`) replaces every step of the scale, the pill, and each
of those hooks with one value, so a card, a dialog, a button, a badge and a field share the same
corner whatever their size. The builder also sets `ha-themes-corner-radius`, which the support
module gives the input chips (`ha-input-chip`), since they lock a 16px pill on their own host,
and the colored icon tiles of Settings (see [Settings icon tiles](#settings-icon-tiles)).
`ha-border-radius-circle` (50%) and `ha-border-radius-square` (0) are shapes rather than
sizes and stay, so avatars, round icon buttons, radio buttons and switch thumbs remain
circles. The frontend's derived radii stay
positive: the inner card edges subtract 1–2px, the control switch subtracts its 6px padding
from `ha-border-radius-6xl`, and the Web Awesome checkbox takes the smaller of 37.5 % of its
size and `wa-border-radius-s`.

Some radii are literals in component styles that no variable reaches, and keep their stock
shape: the switch tracks (pill), and a few 10px corners that a parent sets on its children —
the filter chips and the search field of the data table toolbars, one `ha-control-select`.
`corner_radius: false` keeps the frontend's radii.

## Backdrop blur

Components expose `backdrop-filter` hooks, all unset (`none`) by default:

| Hook | Element | Background it blurs through |
| --- | --- | --- |
| `app-header-backdrop-filter` | Fixed top bar of dashboards (`hui-root`) and the overview | `ha-themes-dashboard-header-background` (see below) |
| `ha-card-backdrop-filter` | Every `ha-card` | `ha-card-background` (falls back to `card-background-color`) |
| `ha-dialog-surface-backdrop-filter` | Dialog and bottom-sheet surfaces | `ha-dialog-surface-background` |
| `ha-dialog-scrim-backdrop-filter` | The page behind a modal (default `brightness(68%)`) | the scrim itself |
| `ha-bottom-sheet-*-backdrop-filter` | Bottom sheets on mobile; fall back to the dialog hooks | — |

A blur is only visible through a translucent background, so each hook needs its background
token set to a color with alpha. Settings pages scroll in a container that starts below
the top bar, so nothing passes underneath their header; the effect shows on dashboards,
the overview and dialogs. The sidebar and dropdown menus have no hook.

A dialog blurs the page through the scrim, so it sees the page already dimmed by
`brightness(68%)`: a translucent white surface then renders as a cool grey, darker than the
page and two-toned against the opaque panes inside the dialog. The builder pairs the stock
scrim with `brightness(147%)` on the dialog surface, which reverses the dimming under the
dialog only, and leaves out `saturate()` there so colored content behind the dialog does not
tint it.

Keep `app-header-background-color` opaque: only the dashboard header reads the blur, but
about a hundred other places paint that color without one (the notification drawer,
settings page toolbars, top app bars, tab scroll buttons, badge borders), and content behind
them would show through unblurred. The builder writes the translucent color to
`ha-themes-dashboard-header-background` instead, and the support module paints the
dashboard header (and its tab scroll buttons) with it, falling back to
`app-header-background-color` when a theme does not set it.

Keep `card-background-color` opaque and make only `ha-card-background` translucent.
`card-background-color` is the page plane, but sticky table headers and pickers opened as a
bottom sheet still paint it over other content; [Creating a theme](creating-a-theme.md#roles) lists its consumers and how the
support module raises the dropdown menus and lists among them. `app-theme-color` (the
browser's theme color) should stay an opaque hex value.

## Popup scrim

Dropdown menus (`ha-dropdown`, also behind `ha-select`) and picker popovers (`wa-popover`, used
by `ha-generic-picker`) open in the top layer through a `wa-popup`, with no backdrop of their
own: the page stays as bright as before. The support module gives that popup's `::backdrop`
the filter in `ha-themes-popup-scrim-filter` (`brightness(85%)` on every theme built here),
faded in over `ha-animation-duration-fast`. Tooltips use the same `wa-popup` but are hosted by
`wa-tooltip`, which the module leaves alone, so hovering never dims the page.

A popover's backdrop never takes pointer events, and a menu closes on the press of a click
outside it, so in stock Home Assistant that click also activates the link, button or row under
it. Behind the scrim the page reads as inert, as behind a dialog, so while a dimmed menu is open
the support module lets a press that starts outside every open menu close it as before and
swallows the click it ends in. Clicks inside a menu, keyboard activation and clicks with no
dimmed menu open (or with `ha-themes-popup-scrim-filter: none`) are untouched. Picker popovers
open as modal dialogs, which already make the page under them inert.

## Known upstream issues (frontend 20261028.4)

| Issue | Effect | Workaround applied by the builder |
| --- | --- | --- |
| `body` font is a hard-coded literal | Sidebar, header and banners ignore `ha-font-family-body` | Support module binds `body` to the variable |
| Dark `ha-color-fill-neutral-quiet-active` references `--ha-color-neutral-00` | Resolves to nothing in dark mode | Set to `neutral.05` |
| Dark `ha-color-surface-lower-inverted` references `--ha-color-90` | Resolves to nothing in dark mode | Set to `neutral.90` |
| Dark mode declares `ha-color-border-normal` instead of `ha-color-border-primary-normal` | The primary normal border keeps its light value in dark mode | Set `ha-color-border-primary-normal` to `primary.50` in dark |
| Dark `wa-form-control-padding-inline` has the next stylesheet glued onto it, and the inline value survives a switch back to light | Web Awesome form controls lose their inline padding and the gap before end slots (units, icons) in both modes | Set to `var(--ha-space-3)` in both modes |

`ha-themes catalog` re-detects broken references on every capture and lists them in
[tokens-global.md](tokens-global.md#broken-upstream-references).
