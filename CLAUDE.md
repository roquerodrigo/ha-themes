# CLAUDE.md

Guidance for Claude Code (claude.ai/code) agents working in this repository.

## Always read `CODE_STYLE.md` first

Before creating, renaming or restructuring any file/class/function, **read
[`CODE_STYLE.md`](./CODE_STYLE.md)**. It is the single source of truth for conventions of the
shipped integration. For what the project does and the commands, see
[`README.md`](./README.md).

## Two halves

- `custom_components/ha_themes/` — the integration HACS installs. Strict rules (`ruff`
  `ALL`, strict mypy, 90 % coverage gate).
- `toolkit/` — development tooling: token capture in Google Chrome, reference docs,
  palette generation and the theme builder. Never shipped; lighter lint config in
  `toolkit/ruff.toml`; run it with `scripts/ha-themes`.

The builder writes into the integration: `custom_components/ha_themes/themes/*.yaml` and
`custom_components/ha_themes/frontend/ha-themes.js` are **generated** from `themes-src/`
and `toolkit/ha_theme_kit/support/ha-themes.js`. Never edit them by hand; rebuild and
commit the output with the source change.

## Verification workflow

**After every code change, run lint then tests before declaring the task done** —
`scripts/lint`, or directly:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
```

The coverage gate measures only the integration, so a toolkit-only run needs
`uv run pytest toolkit/tests --no-cov`. `toolkit/tests/test_generated_files.py` rebuilds
the themes and the support module in memory and fails when the committed output is stale.

Changes to themes or the support module also need `scripts/ha-themes build --strict` and a
look in the browser (`scripts/ha-themes preview`). Browser sessions keep the themes they apply
inside their own page, so sessions can run side by side, and hand the dev instance back with
the last tested theme selected and dark mode on automatic.

## Bumping the Home Assistant version

Pinned in four places that must move together: `homeassistant`,
`home-assistant-frontend` and `pytest-homeassistant-custom-component` (whose
`requires_dist` must list the same `homeassistant`) in `pyproject.toml`, and
`homeassistant` in `hacs.json`. Then re-capture the catalog and review the frontend copies
kept by hand (README → Updating to a new Home Assistant release). Dependabot ignores the
three packages, and `toolkit/tests/test_pinned_versions.py` fails while any of the four
pins or `catalog/tokens.json` disagree with the installed packages. pytest, pytest-asyncio
and pytest-cov come exact-pinned from `pytest-homeassistant-custom-component`; do not pin
them again in `pyproject.toml`.

## Conventions not obvious from the code

- Home Assistant only loads themes from the `frontend: themes:` YAML and replaces any other
  theme on `frontend.reload_themes`, so the integration installs files into
  `themes/ha_themes/` and reloads (only when a file changed or the frontend lacks the
  themes), instead of injecting themes into `hass.data`. Repair
  issues cover configurations that do not include the themes directory and reloads that
  fail (for example on an invalid theme elsewhere in the configuration).
- The support module is added with `add_extra_js_url` under a content-hash URL: both the
  HTTP cache (31 days on static files) and the frontend service worker
  (stale-while-revalidate) would otherwise serve old copies. Lovelace resources are not an
  option — they only load on Lovelace dashboards.
- Static routes cannot be removed from the running HTTP server, so whether the module's
  path is registered is process-wide state kept under a `HassKey`, the one deliberate use of
  `hass.data`.
