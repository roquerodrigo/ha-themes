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
| Typography | `ha-font-{family,size,weight}-*`, `ha-line-height-*` | Families, a size scale multiplied by `ha-font-size-scale`, weights. |
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

Themes can only set CSS variables, so they cannot load web fonts. To use a font that is not
installed on every device, load its stylesheet globally with a small module registered as
`frontend: extra_module_url:` (the builder generates one per theme that declares
`typography.stylesheet`). The module runs on every page, and fonts declared on the
document are visible inside every shadow root.

## Known upstream issues (frontend 20260826.7)

| Issue | Effect | Workaround applied by the builder |
| --- | --- | --- |
| Dark `ha-color-fill-neutral-quiet-active` references `--ha-color-neutral-00` | Resolves to nothing in dark mode | Set to `neutral.05` |
| Dark `ha-color-surface-lower-inverted` references `--ha-color-90` | Resolves to nothing in dark mode | Set to `neutral.90` |
| Dark mode declares `ha-color-border-normal` instead of `ha-color-border-primary-normal` | The primary normal border keeps its light value in dark mode | Set `ha-color-border-primary-normal` to `primary.50` in dark |

`ha-themes catalog` re-detects broken references on every capture and lists them in
[tokens-global.md](tokens-global.md#broken-upstream-references).
