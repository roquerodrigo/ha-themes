from dataclasses import replace

from ha_theme_kit.theme.definition import ThemeDefinition

SYSTEM_UI_FONT_STACK = (
    'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
)
PRESERVED_TYPOGRAPHY_ROLES = ("code", "size_scale")


def system_ui_variant(definition: ThemeDefinition) -> ThemeDefinition:
    typography = {
        role: value
        for role, value in definition.typography.items()
        if role in PRESERVED_TYPOGRAPHY_ROLES
    }
    typography.update(dict.fromkeys(("body", "heading", "longform"), SYSTEM_UI_FONT_STACK))
    return replace(
        definition,
        slug=f"{definition.slug}-system-ui",
        name=f"{definition.name} System UI",
        typography=typography,
    )


def theme_family(definition: ThemeDefinition) -> list[ThemeDefinition]:
    return [definition, system_ui_variant(definition)]
