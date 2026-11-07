# Contribution guidelines

Contributing to this project should be as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features

## Github is used for everything

Github is used to host code, to track issues and feature requests, as well as accept pull requests.

Pull requests are the best way to propose changes to the codebase.

1. Fork the repo and create your branch from `main`.
2. If you've changed something, update the documentation.
3. Make sure `scripts/lint` passes: it runs the format check, lint, type check and tests, as CI does.
4. Test your contribution against the local Home Assistant instance.
5. Issue that pull request!

## Any contributions you make will be under the MIT Software License

In short, when you submit code changes, your submissions are understood to be under the same [MIT License](http://choosealicense.com/licenses/mit/) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using Github's [issues](../../issues)

GitHub issues are used to track public bugs.
Report a bug by [opening a new issue](../../issues/new/choose); it's that easy!

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can.
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## Use a Consistent Coding Style

The integration is checked with every [ruff](https://docs.astral.sh/ruff/) rule and a strict
[mypy](https://mypy-lang.org/) configuration (both in `pyproject.toml`; the dev tooling under `toolkit/` has lighter rules in
`toolkit/ruff.toml`), and the tests must keep coverage at 90 % or more. See
[`CODE_STYLE.md`](CODE_STYLE.md) for the conventions. Run `scripts/lint` before sending a PR.

## Test your code modification

Requires Python 3.14, [uv](https://docs.astral.sh/uv/) and Google Chrome. The full workflow is in
the [Development](README.md#development) section of the README.

```bash
scripts/setup                      # install the development environment
scripts/dev-server                 # local Home Assistant on :8123 running the integration
scripts/ha-themes onboard          # first run only: test user + the integration
```

The dev server runs Home Assistant with [`dev/config/configuration.yaml`](dev/config/configuration.yaml)
and mirrors `custom_components/ha_themes` into the dev configuration on every start.

Themes are defined in `themes-src/`; `themes/` and `frontend/` inside
`custom_components/ha_themes/` are generated, so never edit them by hand. After changing a theme,
its roles or palettes, the builder or the support module, run `scripts/ha-themes build --strict`,
commit the regenerated files and restart the dev server to see the change. Check visual changes
in Google Chrome in light and dark mode.

## License

By contributing, you agree that your contributions will be licensed under its MIT License.
