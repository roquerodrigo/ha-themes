from dataclasses import dataclass

from ha_theme_kit.color.oklch import hex_to_rgba
from ha_theme_kit.theme.chart_palette import ChartSettings, build_chart_colors, series_for_mode
from ha_theme_kit.theme.definition import MODES, ThemeDefinition
from ha_theme_kit.theme.entity_palette import EntityColorSettings, build_entity_colors
from ha_theme_kit.theme.palette_resolver import PaletteResolver
from ha_theme_kit.theme.roles import (
    BACKDROP_BLUR_FILTERS,
    FLAT_ELEVATION,
    ROLE_DEFAULTS,
    ROLE_FALLBACKS,
    ROLE_TOKENS,
    TRANSLUCENT_SURFACES,
    TYPOGRAPHY_BRIDGE,
    UPSTREAM_FIXES,
)

FONT_STYLESHEET_KEY = "stylesheet"
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
    resolver = PaletteResolver(definition.palette)

    base = resolver.core_tokens() | TYPOGRAPHY_BRIDGE
    for role, value in definition.typography.items():
        if role == FONT_STYLESHEET_KEY:
            continue
        if role not in TYPOGRAPHY_TOKENS:
            raise ValueError(f"unknown typography role {role!r}")
        base[TYPOGRAPHY_TOKENS[role]] = str(value)
    if not definition.shadows:
        base.update(FLAT_ELEVATION)
    if definition.backdrop_blur:
        base.update(BACKDROP_BLUR_FILTERS)
    base.update(_resolve_all(resolver, definition.tokens.get("base", {})))

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
        resolved_roles[mode] = _resolve_all(resolver, mode_roles)
        tokens = _resolve_all(resolver, UPSTREAM_FIXES.get(mode, {}))
        tokens |= build_entity_colors(entity_settings, resolver, mode)
        if chart_settings:
            chart_series[mode] = series_for_mode(chart_settings, resolver, mode)
            tokens |= build_chart_colors(chart_series[mode])
        for role, value in resolved_roles[mode].items():
            tokens.update(dict.fromkeys(ROLE_TOKENS[role], value))
        if definition.backdrop_blur:
            tokens.update(_translucent_surfaces(resolved_roles[mode]))
        tokens.update(_resolve_all(resolver, definition.tokens.get(mode, {})))
        modes[mode] = tokens

    return BuiltTheme(definition, base, modes, resolved_roles, chart_series)


def _translucent_surfaces(roles: dict[str, str]) -> dict[str, str]:
    surfaces = {
        token: hex_to_rgba(roles[role], alpha)
        for token, (role, alpha) in TRANSLUCENT_SURFACES.items()
    }
    surfaces["app-theme-color"] = roles["header_background"]
    return surfaces


def _resolve_all(resolver: PaletteResolver, values: dict[str, str]) -> dict[str, str]:
    return {key: resolver.resolve(str(value)) for key, value in values.items()}
