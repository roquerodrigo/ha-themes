import re
from dataclasses import dataclass

from ha_theme_kit.color.oklch import contrast_ratio
from ha_theme_kit.color.vision import CategoricalReport, check_categorical
from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.builder import BuiltTheme
from ha_theme_kit.theme.roles import CONTRAST_PAIRS, FLAT_ELEVATION, PROJECT_TOKEN_PREFIX

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

    @property
    def ok(self) -> bool:
        return (
            not self.unknown_tokens
            and not self.shadowed_base_tokens
            and all(result.passes for result in self.contrast)
            and all(report.passes for report in self.charts)
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
    charts = [
        check_categorical(series, mode, theme.roles[mode]["surface"])
        for mode, series in theme.chart_series.items()
    ]
    shadowed, mode_dependent = _check_base_overrides(theme, catalog)
    return ValidationReport(unknown, contrast, charts, shadowed, mode_dependent)


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
