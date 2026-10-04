## Summary

<!-- 1-3 bullets describing what changed and why. -->

## Type of change

- [ ] Theme change (colors, roles, palettes, typography)
- [ ] Bug fix
- [ ] New feature
- [ ] Refactor / cleanup
- [ ] Documentation
- [ ] Tooling / CI

## Test plan

- [ ] `scripts/lint` passes (format check, lint, type check and tests with the 90 % coverage gate)
- [ ] `scripts/ha-themes build --strict` ran without errors (if themes, roles, palettes, the builder or the support module changed)
- [ ] The regenerated files under `custom_components/ha_themes/` (`themes/*.yaml`, `frontend/ha-themes.js`) are committed and were not edited by hand
- [ ] Checked in Google Chrome in light and dark mode against the local Home Assistant instance (if the change is visual)
- [ ] `previews/` regenerated with `scripts/ha-themes preview` (if the change is visual)
- [ ] Reference docs regenerated with `scripts/ha-themes docs` (if the token catalog or the docs generator changed)

## Checklist

- [ ] The pull request title follows Conventional Commits (it becomes the changelog entry)
- [ ] Version files left untouched: the release pull request bumps `manifest.json`, `pyproject.toml` and `uv.lock`
- [ ] Code is in English (only `translations/<locale>.json` follows the locale)
- [ ] All translation locales updated (if user-facing strings changed)
- [ ] One top-level class per file in the integration
- [ ] README, CONTRIBUTING or CODE_STYLE updated if behavior, architecture or workflow changed
