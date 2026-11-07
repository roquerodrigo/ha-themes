# Changelog

## 1.0.0 (2026-11-07)

Introduces the HA Themes integration with Anthropic themes in light and dark modes, requiring Home Assistant 2026.11.0 or later.

### New features

- Adds the HA Themes integration with Anthropic and Anthropic System UI themes, each available in light and dark mode.
- Themes are installed and reloaded automatically and removed with the integration. Repair issues appear when the themes folder is not included or a reload fails.
- A support module applies the theme font across the whole interface and loads web fonts on demand.
