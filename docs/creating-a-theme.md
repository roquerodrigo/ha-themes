# Creating a theme

A theme is one YAML file in `themes-src/`. The builder expands it into the full token set
under `themes/<slug>.yaml`, validates every key against the token catalog and checks text
contrast. You decide on a palette and a handful of roles; the builder writes the ~100
tokens Home Assistant needs.

```bash
cp themes-src/anthropic.yaml themes-src/my-theme.yaml
uv run ha-themes build my-theme --strict
uv run ha-themes preview my-theme
```

## Schema

```yaml
name: My Theme                 # theme name shown in the profile picker
description: One paragraph.

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
  longform: "Lora, Georgia, serif"
  code: "JetBrains Mono, monospace"
  size_scale: "1"
  stylesheet: "https://fonts.googleapis.com/css2?family=…"   # generates a font loader

roles:                         # optional per mode; unset roles use the defaults below
  light:
    background: "#faf9f5"
    surface: "#ffffff"
  dark:
    background: "#262624"

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
| `background` | `primary-background-color`, `clear-background-color` | `{neutral.95}` | `{neutral.05}` |
| `surface` | `card-background-color`, `ha-color-surface-default` | `#ffffff` | `{neutral.10}` |
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
| `state_active` | `state-active-color` | — | — |
| `scrollbar` | `scrollbar-thumb-color` | `{neutral.70}` | `{neutral.40}` |
| `shadow` | `shadow-color` | `rgba(0, 0, 0, 0.16)` | `rgba(0, 0, 0, 0.48)` |
| `input_fill` | `input-fill-color` | `{neutral.95}` | `{neutral.90@0.05}` |
| `code_background` | `markdown-code-background-color` | `{neutral.95}` | `{neutral.05}` |
| `sidebar_background` / `sidebar_text` / `sidebar_selected` | `sidebar-*` | — | — |
| `header_background` / `header_text` | `app-header-*` | — | — |

Roles marked — are only written when set; otherwise the frontend's derived default applies
(the sidebar follows the card background, the header follows the sidebar).

### Validation

`ha-themes build` reports, per theme:

- tokens that do not exist in the captured frontend (typos, or tokens removed upstream);
- WCAG contrast for text on background and surface (4.5:1), link on surface (4.5:1), and
  primary, error and on-primary text (3:1).

`--strict` turns any failure into a non-zero exit code.

## Installing a theme

1. Copy `themes/<slug>.yaml` into the Home Assistant `config/themes/` directory, with
   `frontend: themes: !include_dir_merge_named themes` in `configuration.yaml`.
2. If the theme has a font loader, copy `www/ha-themes/<slug>-fonts.js` to
   `config/www/ha-themes/` and register it:

   ```yaml
   frontend:
     extra_module_url:
       - /local/ha-themes/<slug>-fonts.js
   ```

3. Call `frontend.reload_themes` (a restart is only needed after adding the module), then
   pick the theme in the user profile.
