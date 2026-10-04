from dataclasses import dataclass, field

from ha_theme_kit.color.css_color import contrast_on
from ha_theme_kit.color.vision import CategoricalReport, check_categorical
from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.builder import BuiltTheme
from ha_theme_kit.theme.entity_separation import EntitySeparationReport, check_entity_separation
from ha_theme_kit.theme.form_separation import FormSeparationReport, check_form_separation
from ha_theme_kit.theme.loud_fills import (
    LOUD_FILL_STATES,
    LOUD_FILL_STATUSES,
    ON_COLOR_CONTRAST_FLOOR,
    fill_token,
    on_color_token,
)
from ha_theme_kit.theme.mode_colors import ModeColors
from ha_theme_kit.theme.roles import CONTRAST_PAIRS, FLAT_ELEVATION, PROJECT_TOKEN_PREFIX
from ha_theme_kit.theme.status_fills import StatusFillReport, check_status_fills
from ha_theme_kit.theme.tinted_on_colors import measure_tinted_pairs
from ha_theme_kit.theme.toast_colors import TOAST_BACKGROUND_TOKEN, measure_toast_pairs
from ha_theme_kit.theme.token_readers import unread_role_tokens
from ha_theme_kit.theme.track_contrast import TRACK_ROLE, measure_track_pairs


@dataclass(frozen=True)
class ContrastResult:
    mode: str
    foreground_role: str
    background_role: str
    ratio: float | None
    """None when either side does not resolve to a color the check can measure."""
    minimum: float

    @property
    def passes(self) -> bool:
        return self.ratio is not None and self.ratio >= self.minimum


@dataclass(frozen=True)
class ValidationReport:
    unknown_tokens: list[str]
    contrast: list[ContrastResult]
    charts: list[CategoricalReport]
    shadowed_base_tokens: list[str]
    mode_dependent_base_tokens: list[str]
    status_fills: StatusFillReport | None = None
    form_separation: FormSeparationReport | None = None
    entity_separation: EntitySeparationReport | None = None
    unread_role_tokens: list[str] = field(default_factory=list)
    """Tokens a role writes that neither the frontend nor the support module reads."""

    @property
    def ok(self) -> bool:
        return (
            not self.unknown_tokens
            and not self.unread_role_tokens
            and not self.shadowed_base_tokens
            and all(result.passes for result in self.contrast)
            and all(report.passes for report in self.charts)
            and (self.status_fills is None or self.status_fills.passes)
            and (self.form_separation is None or self.form_separation.passes)
            and (self.entity_separation is None or self.entity_separation.passes)
        )


def validate_theme(theme: BuiltTheme, catalog: TokenCatalog) -> ValidationReport:
    unknown = sorted(
        key
        for key in theme.all_token_keys()
        if catalog.find(key) is None and not key.startswith(PROJECT_TOKEN_PREFIX)
    )
    contrast = [
        ContrastResult(
            mode,
            foreground,
            background,
            contrast_on(colors.role(foreground), colors.opaque_role(background)),
            minimum,
        )
        for mode in theme.roles
        for colors in (ModeColors.of_theme(theme, mode, catalog),)
        for foreground, background, minimum in CONTRAST_PAIRS
    ]
    contrast.extend(_check_loud_fills(theme, catalog))
    contrast.extend(_check_tinted_on_colors(theme, catalog))
    contrast.extend(_check_tracks(theme, catalog))
    contrast.extend(_check_toasts(theme, catalog))
    charts = [
        check_categorical(series, mode, _opaque_surface(theme, mode, catalog))
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
        check_entity_separation(theme, catalog),
        unread_role_tokens(
            set().union(*(mode_roles.keys() for mode_roles in theme.roles.values())), catalog
        ),
    )


def _check_loud_fills(theme: BuiltTheme, catalog: TokenCatalog) -> list[ContrastResult]:
    """Every loud fill state against its on-color, as the frontend resolves them per mode."""
    return [
        ContrastResult(
            mode,
            on_color_token(status),
            fill_token(status, state),
            contrast_on(
                colors.token(on_color_token(status)),
                colors.opaque_token(fill_token(status, state)),
            ),
            ON_COLOR_CONTRAST_FLOOR,
        )
        for mode in theme.modes
        for colors in (ModeColors.of_theme(theme, mode, catalog),)
        for status in ("primary", *LOUD_FILL_STATUSES)
        for state in LOUD_FILL_STATES
    ]


def _check_tinted_on_colors(theme: BuiltTheme, catalog: TokenCatalog) -> list[ContrastResult]:
    return [
        ContrastResult(
            pair.mode, pair.on_color_token, pair.backdrop_token, pair.ratio, pair.minimum
        )
        for mode in theme.modes
        for pair in measure_tinted_pairs(ModeColors.of_theme(theme, mode, catalog))
    ]


def _check_tracks(theme: BuiltTheme, catalog: TokenCatalog) -> list[ContrastResult]:
    return [
        ContrastResult(pair.mode, TRACK_ROLE, pair.backdrop_role, pair.ratio, pair.minimum)
        for mode in theme.roles
        for pair in measure_track_pairs(ModeColors.of_theme(theme, mode, catalog))
    ]


def _check_toasts(theme: BuiltTheme, catalog: TokenCatalog) -> list[ContrastResult]:
    return [
        ContrastResult(
            pair.mode, pair.on_color_token, TOAST_BACKGROUND_TOKEN, pair.ratio, pair.minimum
        )
        for mode in theme.modes
        for pair in measure_toast_pairs(ModeColors.of_theme(theme, mode, catalog))
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


def _opaque_surface(theme: BuiltTheme, mode: str, catalog: TokenCatalog) -> str | None:
    surface = ModeColors.of_theme(theme, mode, catalog).opaque_role("surface")
    return None if surface is None else surface.to_hex()
