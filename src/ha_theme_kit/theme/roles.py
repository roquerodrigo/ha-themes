"""Design roles a theme author decides on, and the frontend tokens each role drives.

Semantic `ha-color-*` tokens already derive from the core palette, so the roles below
cover what the palette cannot reach: application tokens the frontend hard-codes per mode.

`card-background-color` belongs to the page plane: the frontend paints it on elements that
sit directly on the page (the logbook's floating date, data tables, headers). Raised
surfaces have their own hooks — `ha-card-background`, the Material and Web Awesome
surfaces — so cards, menus and dialogs keep the surface tone.
"""

ROLE_TOKENS: dict[str, tuple[str, ...]] = {
    "background": ("primary-background-color", "clear-background-color", "card-background-color"),
    "surface": (
        "ha-card-background",
        "ha-color-surface-default",
        "mdc-theme-surface",
        "wa-color-surface-default",
    ),
    "surface_variant": ("secondary-background-color",),
    "text": ("primary-text-color", "ha-color-text-primary"),
    "text_secondary": ("secondary-text-color", "ha-color-text-secondary"),
    "text_disabled": ("disabled-text-color", "ha-color-text-disabled"),
    "text_on_primary": ("text-primary-color",),
    "primary": ("primary-color",),
    "primary_light": ("light-primary-color",),
    "primary_dark": ("dark-primary-color",),
    "primary_darker": ("darker-primary-color",),
    "accent": ("accent-color",),
    "link": ("ha-color-text-link",),
    "divider": ("divider-color", "outline-color"),
    "outline_hover": ("outline-hover-color",),
    "error": ("error-color",),
    "warning": ("warning-color",),
    "success": ("success-color",),
    "info": ("info-color",),
    "state_icon": ("state-icon-color",),
    "state_active": ("state-active-color",),
    "scrollbar": ("scrollbar-thumb-color",),
    "shadow": ("shadow-color",),
    "input_fill": ("input-fill-color",),
    "code_background": ("markdown-code-background-color",),
    "sidebar_background": ("sidebar-background-color",),
    "sidebar_text": ("sidebar-text-color",),
    "sidebar_selected": ("sidebar-selected-text-color", "sidebar-selected-icon-color"),
    "header_background": ("app-header-background-color",),
    "header_text": ("app-header-text-color",),
    "brand_icon": ("ha-themes-brand-icon-color",),
}

ROLE_DEFAULTS: dict[str, dict[str, str]] = {
    "light": {
        "background": "{neutral.95}",
        "surface": "#ffffff",
        "surface_variant": "{neutral.90}",
        "text": "{neutral.05}",
        "text_secondary": "{neutral.40}",
        "text_disabled": "{neutral.70}",
        "text_on_primary": "#ffffff",
        "primary": "{primary.40}",
        "primary_light": "{primary.80}",
        "primary_dark": "{primary.30}",
        "primary_darker": "{primary.20}",
        "accent": "{orange.60}",
        "link": "{primary.40}",
        "divider": "{neutral.05@0.12}",
        "outline_hover": "{neutral.05@0.24}",
        "error": "{red.50}",
        "warning": "{orange.60}",
        "success": "{green.50}",
        "info": "{primary.50}",
        "state_icon": "{primary.30}",
        "scrollbar": "{neutral.70}",
        "shadow": "rgba(0, 0, 0, 0.16)",
        "input_fill": "{neutral.95}",
        "code_background": "{neutral.95}",
    },
    "dark": {
        "background": "{neutral.05}",
        "surface": "{neutral.10}",
        "surface_variant": "{neutral.20}",
        "text": "{neutral.90}",
        "text_secondary": "{neutral.60}",
        "text_disabled": "{neutral.40}",
        "text_on_primary": "#ffffff",
        "primary": "{primary.50}",
        "primary_light": "{primary.30}",
        "primary_dark": "{primary.60}",
        "primary_darker": "{primary.70}",
        "accent": "{orange.60}",
        "link": "{primary.60}",
        "divider": "{neutral.90@0.12}",
        "outline_hover": "{neutral.90@0.24}",
        "error": "{red.60}",
        "warning": "{orange.60}",
        "success": "{green.60}",
        "info": "{primary.60}",
        "state_icon": "{primary.60}",
        "scrollbar": "{neutral.40}",
        "shadow": "rgba(0, 0, 0, 0.48)",
        "input_fill": "{neutral.90@0.05}",
        "code_background": "{neutral.05}",
    },
}

ROLE_FALLBACKS: dict[str, str] = {
    "sidebar_background": "background",
    "header_background": "background",
    "brand_icon": "primary",
}
"""Roles that follow another role unless a theme sets them: chrome blends into the page, and
generic integration icons take the primary color."""

PROJECT_TOKEN_PREFIX = "ha-themes-"
"""Variables read by the support module rather than the frontend."""

FLAT_ELEVATION: dict[str, str] = dict.fromkeys(
    (
        "ha-box-shadow-s",
        "ha-box-shadow-m",
        "ha-box-shadow-l",
        "wa-shadow-s",
        "wa-shadow-m",
        "wa-shadow-l",
        "ha-card-box-shadow",
        "dialog-box-shadow",
        "bar-box-shadow",
    ),
    "0 0 0 0 transparent",
) | {"md-sys-color-shadow": "transparent"}
"""A transparent zero shadow instead of `none` stays valid inside comma-separated shadow lists."""

BACKDROP_BLUR_FILTERS: dict[str, str] = {
    "app-header-backdrop-filter": "blur(20px) saturate(160%)",
    "ha-card-backdrop-filter": "blur(16px) saturate(140%)",
    "ha-dialog-surface-backdrop-filter": "blur(24px) saturate(160%)",
    "ha-dialog-scrim-backdrop-filter": "blur(6px) brightness(68%)",
}

TRANSLUCENT_SURFACES: dict[str, tuple[str, float]] = {
    "app-header-background-color": ("header_background", 0.72),
    "ha-card-background": ("surface", 0.8),
    "ha-dialog-surface-background": ("surface", 0.85),
}
"""A backdrop filter only shows through a translucent background, so each blurred element
also gets its role color with alpha."""

TYPOGRAPHY_BRIDGE: dict[str, str] = {
    "md-ref-typeface-plain": "var(--ha-font-family-body)",
    "mdc-typography-font-family": "var(--ha-font-family-body)",
}
"""Material components fall back to a literal Roboto instead of the HA body font."""

UPSTREAM_FIXES: dict[str, dict[str, str]] = {
    "dark": {
        "ha-color-fill-neutral-quiet-active": "{neutral.05}",
        "ha-color-surface-lower-inverted": "{neutral.90}",
        "ha-color-border-primary-normal": "{primary.50}",
    },
}
"""Dark defaults that reference undeclared tokens in frontend 20260826.7 (see docs)."""

CONTRAST_PAIRS: tuple[tuple[str, str, float], ...] = (
    ("text", "background", 4.5),
    ("text", "surface", 4.5),
    ("text_secondary", "surface", 4.5),
    ("text_on_primary", "primary", 3.0),
    ("link", "surface", 4.5),
    ("primary", "surface", 3.0),
    ("error", "surface", 3.0),
)
