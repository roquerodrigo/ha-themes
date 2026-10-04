# How Home Assistant themes work today

Verified against frontend `20260826.7` / Core `2026.9.4`, by reading the shipped theme
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
  `md-ref-typeface-plain` and `mdc-typography-font-family`, which the frontend never sets.
- **Themes cannot load web fonts**, since they only set CSS variables.

The builder sets the two Material tokens to `var(--ha-font-family-body)` in every theme, and
generates one support module, which the integration loads on every page, that binds
`body` to `var(--ha-font-family-body)` and loads the stylesheets of every theme that declares
`typography.stylesheet`. With both in place, an audit of every rendered text node in Chrome
finds only the theme font. Fonts declared on the document are visible inside every shadow
root, and the module runs on every page.

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

The support module recolors them in the browser: it watches every shadow root for
`/api/brands/` images, loads each one into a canvas, and recolors it only when every opaque
pixel is that exact blue, so real logos — multicolored or monochrome in another color — are
never touched. The color comes from `--ha-themes-brand-icon-color`; a theme that does not
set it (the default theme included) gets the original images back.

## Backdrop blur

Components expose `backdrop-filter` hooks, all unset (`none`) by default:

| Hook | Element | Background it blurs through |
| --- | --- | --- |
| `app-header-backdrop-filter` | Fixed top bar of dashboards (`hui-root`) and the overview | `app-header-background-color` |
| `ha-card-backdrop-filter` | Every `ha-card` | `ha-card-background` (falls back to `card-background-color`) |
| `ha-dialog-surface-backdrop-filter` | Dialog and bottom-sheet surfaces | `ha-dialog-surface-background` |
| `ha-dialog-scrim-backdrop-filter` | The page behind a modal (default `brightness(68%)`) | the scrim itself |
| `ha-bottom-sheet-*-backdrop-filter` | Bottom sheets on mobile; fall back to the dialog hooks | — |

A blur is only visible through a translucent background, so each hook needs its background
token set to a color with alpha. Settings pages scroll in a container that starts below
the top bar, so nothing passes underneath their header; the effect shows on dashboards,
the overview and dialogs. The sidebar and dropdown menus have no hook.

Keep `card-background-color` opaque and make only `ha-card-background` translucent: the
former is also used for surfaces that sit on top of other content, such as popovers, and
`app-theme-color` (the browser's theme color) should stay an opaque hex value.

## Known upstream issues (frontend 20260826.7)

| Issue | Effect | Workaround applied by the builder |
| --- | --- | --- |
| `body` font is a hard-coded literal | Sidebar, header and banners ignore `ha-font-family-body` | Support module binds `body` to the variable |
| Dark `ha-color-fill-neutral-quiet-active` references `--ha-color-neutral-00` | Resolves to nothing in dark mode | Set to `neutral.05` |
| Dark `ha-color-surface-lower-inverted` references `--ha-color-90` | Resolves to nothing in dark mode | Set to `neutral.90` |
| Dark mode declares `ha-color-border-normal` instead of `ha-color-border-primary-normal` | The primary normal border keeps its light value in dark mode | Set `ha-color-border-primary-normal` to `primary.50` in dark |

`ha-themes catalog` re-detects broken references on every capture and lists them in
[tokens-global.md](tokens-global.md#broken-upstream-references).
