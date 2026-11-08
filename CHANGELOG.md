# Changelog

## [1.1.1](https://github.com/roquerodrigo/ha-themes/compare/v1.1.0...v1.1.1) (2026-11-08)

### Improvements

- Dropdown menus, selects and picker popovers no longer dim the page behind them; the page keeps its normal brightness while they are open. ([#29](https://github.com/roquerodrigo/ha-themes/pull/29))

## [1.1.0](https://github.com/roquerodrigo/ha-themes/compare/v1.0.0...v1.1.0) (2026-11-08)

Open menus dim the page slightly, icon tiles take the theme's rounded corners, and chart and code editor text now uses the theme font.

### New features

- Dropdown menus, selects and picker popups now dim the page slightly behind them, so the open popup stands out. Tooltips are unchanged. ([#22](https://github.com/roquerodrigo/ha-themes/pull/22))

### Improvements

- Icon tiles in Settings, System, About and the search dialog now use the theme's rounded corners, matching entity icons, and search results follow the theme's colors. ([#24](https://github.com/roquerodrigo/ha-themes/pull/24))

### Bug fixes

- Chart labels, legends and tooltips, and code editor completion details and search fields, now use the theme's font instead of Roboto. ([#25](https://github.com/roquerodrigo/ha-themes/pull/25))

## 1.0.0 (2026-11-07)

### New features

- Adds the HA Themes integration with the Anthropic theme in light and dark modes, installed and reloaded automatically; requires Home Assistant 2026.11.0 or later.
