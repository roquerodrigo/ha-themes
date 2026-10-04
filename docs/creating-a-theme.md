# Creating a theme

A theme is one YAML file in `themes-src/`. The builder expands it into the full token set
under `custom_components/ha_themes/themes/<slug>.yaml`, validates every key against the token catalog and checks text
contrast. You decide on a palette and a handful of roles; the builder writes the ~100
tokens Home Assistant needs.

## House conventions

Every theme built here follows these defaults, so a new theme gets them for free:

- **Sidebar and header share the page background.** `sidebar_background` and
  `header_background` follow the `background` role unless a theme sets them; the 1px
  dividers keep the regions apart.
- **No shadows.** Elevation tokens are flattened (cards, dialogs, menus, tooltips, the
  Material and Web Awesome components). A theme opts back in with `shadows: true`.
- **Backdrop blur.** The header, cards, dialogs and bottom sheets get a translucent
  background (their role color with alpha) plus a `backdrop-filter` blur, and the modal
  scrim blurs the page behind it. A theme opts out with `backdrop_blur: false`.
- **A harmonized entity palette.** The frontend's named colors — which every entity state
  color references — keep their hue and meaning but are restyled per mode: chroma capped to
  the theme's mood and lightness clamped into a band that reads on that mode's surfaces.
  Energy and weather-icon colors follow them.
- **Generic integration icons in the primary color.** The flat blue icons of core
  integrations without a logo follow the theme's `primary` role (see
  [the guide](theming-guide.md#integration-icons)); set the `brand_icon` role to change it.
- **A system-ui variant.** Each definition produces two themes in the same file:
  `<Name>` with its own fonts and `<Name> System UI`, identical but set in the platform's
  UI font (`system-ui`, San Francisco, Segoe UI, Roboto), with no web fonts to download.
- **The whole UI uses the theme font.** Material components get `md-ref-typeface-plain` and
  `mdc-typography-font-family` pointed at `ha-font-family-body`, and the support module
  binds the page body to it (see [the guide](theming-guide.md#fonts)).

```bash
cp themes-src/anthropic.yaml themes-src/my-theme.yaml
scripts/ha-themes build my-theme --strict
scripts/ha-themes preview my-theme
```

## Schema

```yaml
name: My Theme                 # theme name shown in the profile picker
description: One paragraph.
shadows: false                 # optional, default false
backdrop_blur: true            # optional, default true

palette:                       # required: primary, neutral, red, orange, green
  primary: "#d97757"           # a seed: generates steps 05…95 with the frontend's algorithm
  neutral:                     # or an explicit scale (all eleven steps)
    "05": "#141413"
    # …
    "95": "#f0eee6"
  red:
    seed: "#bf4d43"            # or a seed with hand-tuned steps on top
    "05": "#1f0b09"
  orange: "#d08b2c"
  green: "#788c5d"
  blue: "#6a9bcc"              # extra families are allowed, but only usable as references

typography:                    # optional
  body: "Poppins, Arial, sans-serif"
  heading: "Poppins, Arial, sans-serif"
  longform: "Lora, Georgia, serif"   # declared by the frontend, not read by any component yet
  code: "JetBrains Mono, monospace"
  size_scale: "1"
  stylesheet: "https://fonts.googleapis.com/css2?family=…"   # loaded by the support module

roles:                         # optional per mode; unset roles use the defaults below
  light:
    background: "#faf9f5"
    surface: "#ffffff"
  dark:
    background: "#262624"

entity_colors:                 # optional; defaults shown
  chroma_cap: 0.16
  lightness:
    light: [0.50, 0.80]
    dark: [0.62, 0.86]
  pinned:                      # named colors to set explicitly, per mode or for both
    deep-orange: "{primary.50}"
    blue:
      light: "{blue.40}"
      dark: "{blue.50}"

charts:                        # optional; without it the frontend's series stay in place
  series:                      # exactly eight seeds, in order: slot 1 is the opening color
    - "{primary.50}"
    - "{blue.50}"
    # … six more
  lightness:                   # optional per-mode band the seeds are stepped into
    light: [0.50, 0.72]
    dark: [0.58, 0.66]

tokens:                        # optional raw tokens, applied last
  base:                        # mode-independent only
    color-1: "{primary.50}"
  light: {}
  dark: {}
```

### Palette families

`primary`, `neutral`, `red`, `orange` and `green` map to the frontend's core palette
(`ha-color-<family>-<step>`); `red`, `orange` and `green` are the danger, warning and success
families of the semantic layer. Seeds sit at step 50. The generator is a port of the
frontend's own `generateColorPalette` and produces identical values, but its darkest steps
drift towards black — hand-tune `05`–`30` when the theme has a dark mode.

### References

Anywhere a color is expected you can write `{family.step}` or `{family.step@alpha}`:

```yaml
divider: "{neutral.05@0.12}"   # → rgba(20, 20, 19, 0.12)
link: "{primary.30}"           # → #9c4a2e
```

### Roles

| Role | Tokens | Light default | Dark default |
| --- | --- | --- | --- |
| `background` | `primary-background-color`, `clear-background-color`, `card-background-color` | `{neutral.95}` | `{neutral.05}` |
| `surface` | `ha-card-background`, `ha-color-surface-default`, `mdc-theme-surface`, `wa-color-surface-default` | `#ffffff` | `{neutral.10}` |
| `surface_variant` | `secondary-background-color` | `{neutral.90}` | `{neutral.20}` |
| `text` | `primary-text-color`, `ha-color-text-primary` | `{neutral.05}` | `{neutral.90}` |
| `text_secondary` | `secondary-text-color`, `ha-color-text-secondary` | `{neutral.40}` | `{neutral.60}` |
| `text_disabled` | `disabled-text-color`, `ha-color-text-disabled` | `{neutral.70}` | `{neutral.40}` |
| `text_on_primary` | `text-primary-color` | `#ffffff` | `#ffffff` |
| `primary` | `primary-color` | `{primary.40}` | `{primary.50}` |
| `primary_light` / `primary_dark` / `primary_darker` | `light-/dark-/darker-primary-color` | `80` / `30` / `20` | `30` / `60` / `70` |
| `accent` | `accent-color` | `{orange.60}` | `{orange.60}` |
| `link` | `ha-color-text-link` | `{primary.40}` | `{primary.60}` |
| `divider` | `divider-color`, `outline-color` | `{neutral.05@0.12}` | `{neutral.90@0.12}` |
| `outline_hover` | `outline-hover-color` | `{neutral.05@0.24}` | `{neutral.90@0.24}` |
| `error` / `warning` / `success` / `info` | `*-color` | `red.50` / `orange.60` / `green.50` / `primary.50` | `red.60` / `orange.60` / `green.60` / `primary.60` |
| `state_icon` | `state-icon-color` | `{primary.30}` | `{primary.60}` |
| `scrollbar` | `scrollbar-thumb-color` | `{neutral.70}` | `{neutral.40}` |
| `shadow` | `shadow-color` | `rgba(0, 0, 0, 0.16)` | `rgba(0, 0, 0, 0.48)` |
| `input_fill` | `input-fill-color` | `{neutral.95}` | `{neutral.90@0.05}` |
| `code_background` | `markdown-code-background-color` | `{neutral.95}` | `{neutral.05}` |
| `brand_icon` | `ha-themes-brand-icon-color` (read by the support module) | `primary` | `primary` |
| `sidebar_background` / `header_background` | `sidebar-background-color` / `app-header-background-color` | `background` | `background` |
| `sidebar_text` / `sidebar_selected` / `header_text` | `sidebar-*`, `app-header-text-color` | — | — |
| `state_active` | `state-active-color` | — | — |

Roles marked — are only written when set; otherwise the frontend's derived default applies.

`card-background-color` follows `background`, not `surface`: despite its name, the frontend
paints it on elements that sit directly on the page — the logbook's floating date, data
tables, table headers — so a different tone shows up as a stripe. Raised elements read
their own hooks: cards `ha-card-background`, menus and lists `mdc-theme-surface`, Web
Awesome components `wa-color-surface-default`, dialogs `ha-dialog-surface-background`.

### Entity colors

Entity icons, tiles, timelines and the thermostat read `state-*` colors, which point at the
frontend's named colors (`--amber-color` for lights on, `--green-color` for locked, …). The
builder restyles each of the eighteen chromatic named colors in OKLCH: the hue stays, the
chroma is capped at `chroma_cap`, and the lightness is clamped into the mode's band, so the
same palette reads on light and dark surfaces. `light-grey`, `grey`, `dark-grey` and
`disabled` come from the neutral scale. `pinned` replaces any of them outright.

The same colors drive the energy dashboard (`energy-*`: grid in blue, return in purple,
solar in orange, non-fossil in green, battery in teal and pink, gas in red, water in cyan)
and the weather icons (sun in amber, moon in yellow, rain in light blue, clouds and snow
from the neutral scale).

Any `state-<domain>-…-color` can still be set under `tokens` for one-off changes; see the
resolution order in [tokens-components.md](tokens-components.md#dynamic-families).

### Chart series

Graphs, calendars and maps read `color-1` … `color-54` in JavaScript. The eight `series`
seeds are stepped per mode into the lightness band with a chroma floor of 0.105, and must
pass the categorical checks in both modes: lightness band, chroma floor, adjacent
color-vision-deficiency separation (protanopia and deuteranopia simulated with Machado
2009, OKLab ΔE ≥ 6, target 8) and adjacent normal-vision separation (ΔE ≥ 15). Colors
under 3:1 against the card surface are reported but allowed: every chart has a legend and
tooltips. Slots 9–54 repeat the eight hues at lighter and darker steps; past eight series
identity is no longer guaranteed, so prefer fewer series per chart.

The order matters as much as the hues. `scripts/ha-themes palette <slug>` ranks the orders that
keep slot 1 and pass in both modes; pick one and write it into `series`.

### Validation

`ha-themes build` reports, per theme:

- tokens that do not exist in the captured frontend (typos, or tokens removed upstream);
- WCAG contrast for text on background and surface (4.5:1), link on surface (4.5:1), and
  primary, error and on-primary text (3:1);
- the chart series checks above, per mode.

`--strict` turns any failure into a non-zero exit code.

## Shipping a theme

`scripts/ha-themes build` writes every theme family into
`custom_components/ha_themes/themes/<slug>.yaml` and regenerates the support module in
`custom_components/ha_themes/frontend/`. Commit both with the source change; the
integration installs them on the next update (see the README for installation).
