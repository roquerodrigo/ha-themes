import re
from dataclasses import dataclass

from ha_theme_kit.color.oklch import contrast_ratio
from ha_theme_kit.color.vision import CategoricalReport, check_categorical
from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.builder import BuiltTheme
from ha_theme_kit.theme.form_separation import FormSeparationReport, check_form_separation
from ha_theme_kit.theme.loud_fills import (
    LOUD_FILL_STATES,
    LOUD_FILL_STATUSES,
    ON_COLOR_CONTRAST_FLOOR,
    fill_token,
    on_color_token,
)
from ha_theme_kit.theme.roles import CONTRAST_PAIRS, FLAT_ELEVATION, PROJECT_TOKEN_PREFIX
from ha_theme_kit.theme.status_fills import StatusFillReport, check_status_fills
from ha_theme_kit.theme.tinted_on_colors import measure_tinted_pairs
from ha_theme_kit.theme.token_colors import resolve_token_color

HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


@dataclass(frozen=True)
class ContrastResult:
    mode: str
    foreground_role: str
    background_role: str
    ratio: float
    minimum: float

    @property
    def passes(self) -> bool:
        return self.ratio >= self.minimum


@dataclass(frozen=True)
class ValidationReport:
    unknown_tokens: list[str]
    contrast: list[ContrastResult]
    charts: list[CategoricalReport]
    shadowed_base_tokens: list[str]
    mode_dependent_base_tokens: list[str]
    status_fills: StatusFillReport | None = None
    form_separation: FormSeparationReport | None = None

    @property
    def ok(self) -> bool:
        return (
            not self.unknown_tokens
            and not self.shadowed_base_tokens
            and all(result.passes for result in self.contrast)
            and all(report.passes for report in self.charts)
            and (self.status_fills is None or self.status_fills.passes)
            and (self.form_separation is None or self.form_separation.passes)
        )


def validate_theme(theme: BuiltTheme, catalog: TokenCatalog) -> ValidationReport:
    unknown = sorted(
        key
        for key in theme.all_token_keys()
        if catalog.find(key) is None and not key.startswith(PROJECT_TOKEN_PREFIX)
    )
    contrast = []
    for mode, roles in theme.roles.items():
        for foreground, background, minimum in CONTRAST_PAIRS:
            foreground_color, background_color = roles.get(foreground), roles.get(background)
            if not (_is_hex(foreground_color) and _is_hex(background_color)):
                continue
            contrast.append(
                ContrastResult(
                    mode,
                    foreground,
                    background,
                    round(contrast_ratio(foreground_color, background_color), 2),
                    minimum,
                )
            )
    contrast.extend(_check_loud_fills(theme, catalog))
    contrast.extend(_check_tinted_on_colors(theme, catalog))
    charts = [
        check_categorical(series, mode, theme.roles[mode]["surface"])
        for mode, series in theme.chart_series.items()
    ]
    shadowed, mode_dependent = _check_base_overrides(theme, catalog)
    return ValidationReport(
        unknown,
        contrast,
        charts,
        shadowed,
        mode_dependent,
        check_status_fills(theme, catalog),
        check_form_separation(theme, catalog),
    )


def _check_loud_fills(theme: BuiltTheme, catalog: TokenCatalog) -> list[ContrastResult]:
    """Every loud fill state against its on-color, as the frontend resolves them per mode."""
    results = []
    for mode, mode_tokens in theme.modes.items():
        tokens = theme.base | mode_tokens
        for status in ("primary", *LOUD_FILL_STATUSES):
            on_color = resolve_token_color(on_color_token(status), tokens, catalog, mode)
            for state in LOUD_FILL_STATES:
                fill = resolve_token_color(fill_token(status, state), tokens, catalog, mode)
                if on_color is None or fill is None:
                    continue
                results.append(
                    ContrastResult(
                        mode,
                        on_color_token(status),
                        fill_token(status, state),
                        round(contrast_ratio(on_color, fill), 2),
                        ON_COLOR_CONTRAST_FLOOR,
                    )
                )
    return results


def _check_tinted_on_colors(theme: BuiltTheme, catalog: TokenCatalog) -> list[ContrastResult]:
    return [
        ContrastResult(
            pair.mode, pair.on_color_token, pair.backdrop_token, pair.ratio, pair.minimum
        )
        for mode, mode_tokens in theme.modes.items()
        for pair in measure_tinted_pairs(mode, theme.base | mode_tokens, catalog)
    ]


def _check_base_overrides(theme: BuiltTheme, catalog: TokenCatalog) -> tuple[list[str], list[str]]:
    """Split `tokens.base` keys into those a mode overrides and those the frontend themes per mode.

    A mode's keys are applied on top of the base, so a shadowed base value never shows. A base
    key with a dark default replaces that default in dark mode too.
    """
    base_keys = set(theme.definition.tokens.get("base", {}))
    mode_keys = set().union(*(tokens.keys() for tokens in theme.modes.values()))
    shadowed = sorted(base_keys & mode_keys)
    mode_dependent = sorted(
        key
        for key in base_keys - mode_keys - FLAT_ELEVATION.keys()
        if (entry := catalog.find(key)) is not None and entry.dark is not None
    )
    return shadowed, mode_dependent


def _is_hex(value: str | None) -> bool:
    return bool(value and HEX_COLOR.match(value))
