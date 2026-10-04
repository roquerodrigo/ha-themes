import re
from dataclasses import dataclass

from ha_theme_kit.color.oklch import contrast_ratio
from ha_theme_kit.color.vision import CategoricalReport, check_categorical
from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.builder import BuiltTheme
from ha_theme_kit.theme.roles import CONTRAST_PAIRS

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

    @property
    def ok(self) -> bool:
        return (
            not self.unknown_tokens
            and all(result.passes for result in self.contrast)
            and all(report.passes for report in self.charts)
        )


def validate_theme(theme: BuiltTheme, catalog: TokenCatalog) -> ValidationReport:
    unknown = sorted(key for key in theme.all_token_keys() if catalog.find(key) is None)
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
    return ValidationReport(unknown, contrast, charts)


def _is_hex(value: str | None) -> bool:
    return bool(value and HEX_COLOR.match(value))
