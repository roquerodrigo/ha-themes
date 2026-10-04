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
3. Make sure your code lints (run `uv run ruff format --check .`, `uv run ruff check .` and `uv run mypy`).
4. Test your contribution.
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

The project uses [ruff](https://docs.astral.sh/ruff/) (config in `pyproject.toml`). Run `uv run ruff format --check .`, `uv run ruff check .` and `uv run mypy` before sending a PR.

## Test your code modification

This project started from the [ha-integration-blueprint](https://github.com/roquerodrigo/ha-integration-blueprint) template.

Run `scripts/setup` once to create the `uv`-managed virtual environment, then `scripts/develop` to start a stand-alone Home Assistant instance in debug mode with the integration loaded and the included [`configuration.yaml`](./config/configuration.yaml) file.

## Releasing

Releases are cut by `.github/workflows/release.yml` after CI passes on a push to `main`.
release-please keeps a release pull request open with the version bump and the changelog;
merging it tags `vX.Y.Z`, creates the GitHub release and attaches `ha_themes.zip`, the
contents of `custom_components/ha_themes/` that HACS installs (`zip_release` in `hacs.json`).
`tests/test_release_packaging.py` keeps the asset name and the version files consistent.

Versions follow the commit types in `CODE_STYLE.md` (Conventional commits): before 1.0.0
`feat` bumps the minor version, `fix`, `perf`, `revert` and `deps` bump the patch version,
and a breaking change bumps the minor version. `docs`, `refactor`, `deps-dev`, `build`,
`ci`, `test`, `style` and `chore` are hidden from the changelog and do not cut a release
by themselves. release-please creates `CHANGELOG.md` with the first release.

The release workflow needs these one-time steps on GitHub before it can run:

1. Create a fine-grained personal access token for this repository with **Contents** and
   **Pull requests** read and write, and store it as the Actions secret `RELEASE_PLEASE_PAT`.
   The workflow falls back to `GITHUB_TOKEN` without it, and that token cannot open the
   release pull request (Actions may not create pull requests in this repository) and its
   pushes do not trigger the CI and CodeQL checks that `main` requires.
2. Delete the branch `release-please--branches--main--components--ha-themes` left by the
   failed first run, so release-please starts the release pull request from scratch.
3. Re-enable the **Release** workflow (Actions → Release → Enable workflow) and re-run it, or
   push to `main`.
4. Close Dependabot pull request #2: `home-assistant-frontend` is pinned together with Home
   Assistant and the token catalog, and Dependabot now ignores it (README: Updating to a new
   Home Assistant release).

## License

By contributing, you agree that your contributions will be licensed under its MIT License.
