from dataclasses import dataclass

from ha_theme_kit.color.oklch import hex_to_rgba, is_opaque_hex
from ha_theme_kit.theme.chart_palette import ChartSettings, build_chart_colors, series_for_mode
from ha_theme_kit.theme.definition import ThemeDefinition
from ha_theme_kit.theme.entity_palette import EntityColorSettings, build_entity_colors
from ha_theme_kit.theme.loud_fills import build_loud_fills
from ha_theme_kit.theme.modes import MODES
from ha_theme_kit.theme.neutral_layers import FORM_BACKGROUND, layer_neutral_fills
from ha_theme_kit.theme.palette_resolver import PaletteResolver
from ha_theme_kit.theme.roles import (
    BACKDROP_BLUR_FILTERS,
    FIELD_OUTLINE,
    FLAT_ELEVATION,
    ICON_TILE_HARMONY,
    OVERLAY_EDGE,
    ROLE_DEFAULTS,
    ROLE_FALLBACKS,
    ROLE_TOKENS,
    TRANSLUCENT_SURFACES,
    TYPOGRAPHY_BRIDGE,
    UPSTREAM_FIXES,
)
from ha_theme_kit.theme.semantic_layer import build_semantic_colors
from ha_theme_kit.theme.toast_colors import build_toast_colors

FONT_STYLESHEET_KEY = "stylesheet"
FONT_STYLESHEET_TOKEN = "ha-themes-font-stylesheet"
FONT_SIZE_ADJUST_KEY = "size_adjust"
FONT_SIZE_ADJUST_TOKEN = "ha-themes-font-size-adjust"
TYPOGRAPHY_TOKENS = {
    "body": "ha-font-family-body",
    "heading": "ha-font-family-heading",
    "longform": "ha-font-family-longform",
    "code": "ha-font-family-code",
    "size_scale": "ha-font-size-scale",
}


@dataclass(frozen=True)
class BuiltTheme:
    definition: ThemeDefinition
    base: dict[str, str]
    modes: dict[str, dict[str, str]]
    roles: dict[str, dict[str, str]]
    chart_series: dict[str, list[str]]

    @property
    def font_stylesheet(self) -> str | None:
        return self.definition.typography.get(FONT_STYLESHEET_KEY)

    def all_token_keys(self) -> set[str]:
        return set(self.base).union(*(tokens.keys() for tokens in self.modes.values()))


def build_theme(definition: ThemeDefinition) -> BuiltTheme:
    """Mode-dependent values always go under `modes`.

    In dark mode the frontend applies its dark defaults first and the theme's base keys on
    top of them, so a base key would silently win in both modes.
    """
    try:
        return _build(definition)
    except ValueError as error:
        raise ValueError(f"{definition.slug}: {error}") from error


def _build(definition: ThemeDefinition) -> BuiltTheme:
    resolver = PaletteResolver(definition.palette)

    base = resolver.core_tokens() | TYPOGRAPHY_BRIDGE | ICON_TILE_HARMONY
    for role, value in definition.typography.items():
        if role == FONT_STYLESHEET_KEY:
            base[FONT_STYLESHEET_TOKEN] = _css_string(str(value))
            continue
        if role == FONT_SIZE_ADJUST_KEY:
            base[FONT_SIZE_ADJUST_TOKEN] = _x_height_ratio(str(value))
            continue
        if role not in TYPOGRAPHY_TOKENS:
            raise ValueError(f"unknown typography role {role!r}")
        base[TYPOGRAPHY_TOKENS[role]] = str(value)
    if not definition.shadows:
        base.update(FLAT_ELEVATION | OVERLAY_EDGE)
    if definition.backdrop_blur:
        base.update(BACKDROP_BLUR_FILTERS)
    if definition.field_outline:
        base.update(FIELD_OUTLINE)
    base.update(_resolve_all(resolver, definition.tokens.get("base", {}), "tokens.base"))

    entity_settings = EntityColorSettings.from_document(definition.entity_colors)
    chart_settings = ChartSettings.from_document(definition.charts)
    modes: dict[str, dict[str, str]] = {}
    resolved_roles: dict[str, dict[str, str]] = {}
    chart_series: dict[str, list[str]] = {}
    for mode in MODES:
        mode_roles = {**ROLE_DEFAULTS[mode], **definition.roles.get(mode, {})}
        for role, source_role in ROLE_FALLBACKS.items():
            mode_roles.setdefault(role, mode_roles[source_role])
        unknown_roles = set(mode_roles) - set(ROLE_TOKENS)
        if unknown_roles:
            raise ValueError(f"unknown {mode} roles {sorted(unknown_roles)}")
        resolved_roles[mode] = _resolve_all(resolver, mode_roles, f"roles.{mode}")
        tokens = _resolve_all(resolver, UPSTREAM_FIXES.get(mode, {}), f"upstream fixes.{mode}")
        neutral_fills = layer_neutral_fills(mode, resolved_roles[mode], resolver.scales["neutral"])
        tokens |= neutral_fills
        tokens |= build_loud_fills(mode, resolver.scales)
        if FORM_BACKGROUND in neutral_fills and "input_fill" not in definition.roles.get(mode, {}):
            resolved_roles[mode]["input_fill"] = neutral_fills[FORM_BACKGROUND]
        tokens |= build_entity_colors(entity_settings, resolver, mode)
        if chart_settings:
            chart_series[mode] = series_for_mode(chart_settings, resolver, mode)
            tokens |= build_chart_colors(chart_series[mode])
        for role, value in resolved_roles[mode].items():
            tokens.update(dict.fromkeys(ROLE_TOKENS[role], value))
        if definition.backdrop_blur:
            tokens.update(_translucent_surfaces(resolved_roles[mode], mode))
        tokens |= build_semantic_colors(mode, base | tokens, resolver.scales)
        tokens.update(_resolve_all(resolver, definition.tokens.get(mode, {}), f"tokens.{mode}"))
        tokens = build_toast_colors(mode, base | tokens, resolver.scales) | tokens
        modes[mode] = tokens

    return BuiltTheme(definition, base, modes, resolved_roles, chart_series)


def _css_string(value: str) -> str:
    """A bare URL would end the custom property at its first `;`."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _x_height_ratio(value: str) -> str:
    try:
        ratio = float(value)
    except ValueError:
        ratio = 0
    if not 0 < ratio < 1:
        raise ValueError(
            f"typography size_adjust must be an x-height ratio between 0 and 1, got {value!r}"
        )
    return value


def _translucent_surfaces(roles: dict[str, str], mode: str) -> dict[str, str]:
    for role in sorted({role for role, _ in TRANSLUCENT_SURFACES.values()}):
        if not is_opaque_hex(roles[role]):
            raise ValueError(
                f"{mode} role {role!r} must resolve to an opaque hex color while backdrop_blur"
                f" is on (it is given alpha), got {roles[role]!r}"
            )
    surfaces = {
        token: hex_to_rgba(roles[role], alpha)
        for token, (role, alpha) in TRANSLUCENT_SURFACES.items()
    }
    surfaces["app-theme-color"] = roles["header_background"]
    return surfaces


def _resolve_all(resolver: PaletteResolver, values: dict[str, str], section: str) -> dict[str, str]:
    return {key: resolver.resolve(str(value), f"{section}.{key}") for key, value in values.items()}
