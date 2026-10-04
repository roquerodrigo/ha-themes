from dataclasses import dataclass

from ha_theme_kit.theme.definition import MODES, ThemeDefinition
from ha_theme_kit.theme.palette_resolver import PaletteResolver
from ha_theme_kit.theme.roles import (
    FLAT_ELEVATION,
    ROLE_DEFAULTS,
    ROLE_FALLBACKS,
    ROLE_TOKENS,
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
    base.update(_resolve_all(resolver, definition.tokens.get("base", {})))

    modes: dict[str, dict[str, str]] = {}
    resolved_roles: dict[str, dict[str, str]] = {}
    for mode in MODES:
        mode_roles = {**ROLE_DEFAULTS[mode], **definition.roles.get(mode, {})}
        for role, source_role in ROLE_FALLBACKS.items():
            mode_roles.setdefault(role, mode_roles[source_role])
        unknown_roles = set(mode_roles) - set(ROLE_TOKENS)
        if unknown_roles:
            raise ValueError(f"unknown {mode} roles {sorted(unknown_roles)}")
        resolved_roles[mode] = _resolve_all(resolver, mode_roles)
        tokens = _resolve_all(resolver, UPSTREAM_FIXES.get(mode, {}))
        for role, value in resolved_roles[mode].items():
            tokens.update(dict.fromkeys(ROLE_TOKENS[role], value))
        tokens.update(_resolve_all(resolver, definition.tokens.get(mode, {})))
        modes[mode] = tokens

    return BuiltTheme(definition, base, modes, resolved_roles)


def _resolve_all(resolver: PaletteResolver, values: dict[str, str]) -> dict[str, str]:
    return {key: resolver.resolve(str(value)) for key, value in values.items()}
