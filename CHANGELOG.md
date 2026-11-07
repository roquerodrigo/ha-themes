# Changelog

## 1.0.0 (2026-11-07)

HA Themes now supports Home Assistant 2026.11, which requires a newer minimum version, and brings a refined Anthropic theme with outlined fields, a glass icon, entity-colored settings tiles and a fix for web fonts that only load with an active theme.

### Breaking changes

- HA Themes now requires Home Assistant 2026.11.0 or later; the integration no longer loads on earlier releases. ([#16](https://github.com/roquerodrigo/ha-themes/pull/16))

### New features

- The Anthropic theme and its System UI variant gain a glass palette icon and refined colors, with one small corner radius across cards, buttons and fields. ([#15](https://github.com/roquerodrigo/ha-themes/pull/15))
- Form fields lose their fill and use a thin outline that turns primary on focus and danger on invalid input. ([#15](https://github.com/roquerodrigo/ha-themes/pull/15))
- Code editor syntax colors now come from the theme palette, and the code editor reads as a raised surface. ([#15](https://github.com/roquerodrigo/ha-themes/pull/15))
- Settings icon tiles follow the theme's entity colors, and entity icons without a state color use the primary color. ([#15](https://github.com/roquerodrigo/ha-themes/pull/15))
- Wide theme fonts are drawn at the x-height of the default font, so labels fit as in the default theme; the System UI variant keeps the platform font. ([#15](https://github.com/roquerodrigo/ha-themes/pull/15))

### Improvements

- Web fonts load only while a theme that declares them is active, so the default theme and the System UI variants no longer contact Google Fonts. ([#15](https://github.com/roquerodrigo/ha-themes/pull/15))
- The support module stays dormant until a project theme is in use, and brand icons are recolored with the theme of the view or card they sit in. ([#15](https://github.com/roquerodrigo/ha-themes/pull/15))
- Theme installation reloads the themes only when a file changed, and a failed reload or write reports its cause in a repair notice or a setup error. ([#15](https://github.com/roquerodrigo/ha-themes/pull/15))

### Bug fixes

- Selects and pickers are outlined around the whole field, including the arrow, and no longer show the stock fill and bottom line under the outline on Home Assistant 2026.11. ([#17](https://github.com/roquerodrigo/ha-themes/pull/17))
- Map labels and attribution use the theme font instead of the map's own font. ([#18](https://github.com/roquerodrigo/ha-themes/pull/18))
- The map overview panel is raised to the menu surface, and the energy totals card keeps a single tone on Home Assistant 2026.11. ([#18](https://github.com/roquerodrigo/ha-themes/pull/18))
- Browser sessions open their first page only after the login page redirects, so captures no longer fail or land on the wrong dashboard. ([#18](https://github.com/roquerodrigo/ha-themes/pull/18))
- Integration setup no longer fails on Home Assistant 2026.11 because the theme installer now imports the event from its new location. ([#16](https://github.com/roquerodrigo/ha-themes/pull/16))
- Integration entry lists on an integration's page are raised to the card tone again. ([#16](https://github.com/roquerodrigo/ha-themes/pull/16))
