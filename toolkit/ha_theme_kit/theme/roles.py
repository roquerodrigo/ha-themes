"""Design roles a theme author decides on, and the frontend tokens each role drives.

Semantic `ha-color-*` tokens already derive from the core palette, so the roles below
cover what the palette cannot reach: application tokens the frontend hard-codes per mode.

`card-background-color` belongs to the page plane by design: the frontend paints it on
elements that sit directly on the page (data tables and their headers, the logbook's floating
date). Raised elements have their own hooks, mapped to `surface`: `ha-card-background`,
`ha-dialog-surface-background`, `wa-color-surface-default` and `mdc-theme-surface`. The
support module raises the elements that read `card-background-color` from a variable set on
their own host, out of a theme's reach: dropdown menus take `ha-themes-menu-background`, the
integration page's entry lists take `ha-card-background`, and the energy totals table, the one
data table nested inside a card, is cleared so the card shows through.

`primary` and `text_on_primary` drive both the legacy pair (`primary-color` under
`text-primary-color`, also drawn on `accent-color`) and the loud fills of buttons and FABs,
so every filled primary element in a mode shows the same text color.
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
    "text_on_primary": ("text-primary-color", "ha-color-on-primary-loud"),
    "primary": (
        "primary-color",
        "ha-color-fill-primary-loud-resting",
        "ha-color-fill-primary-loud-active",
    ),
    "primary_hover": ("ha-color-fill-primary-loud-hover",),
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
    "menu_background": ("ha-themes-menu-background",),
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
        "primary_hover": "{primary.30}",
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
        "primary_hover": "{primary.60}",
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
    "menu_background": "surface",
}
"""Roles that follow another role unless a theme sets them: chrome blends into the page,
generic integration icons take the primary color, and menus are raised like cards."""

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

TOAST_EDGE_TOKEN = "ha-themes-toast-box-shadow"
"""The toast reads the shared `wa-shadow-l` directly, so the support module paints its edge
with this token instead."""

OVERLAY_EDGE: dict[str, str] = dict.fromkeys(
    ("ha-tooltip-box-shadow", TOAST_EDGE_TOKEN), "0 0 0 1px var(--outline-color)"
)
"""Tooltips and toasts float over the page with only a shadow to separate them, so flat
elevation gives them the 1px outline that menus and cards already have."""

SCRIM_BRIGHTNESS_PERCENT = 68
"""The frontend's own scrim dimming, kept so modals darken the page as in stock HA."""

DIALOG_UNDIMMING_PERCENT = round(100 * 100 / SCRIM_BRIGHTNESS_PERCENT)
"""A dialog blurs the page through the scrim, so it would read as the dimmed page (a cool grey
in light mode, darker than the page) unless its own filter reverses the dimming."""

BACKDROP_BLUR_FILTERS: dict[str, str] = {
    "app-header-backdrop-filter": "blur(20px) saturate(160%)",
    "ha-card-backdrop-filter": "blur(16px) saturate(140%)",
    "ha-dialog-surface-backdrop-filter": f"blur(24px) brightness({DIALOG_UNDIMMING_PERCENT}%)",
    "ha-dialog-scrim-backdrop-filter": f"blur(6px) brightness({SCRIM_BRIGHTNESS_PERCENT}%)",
}

DASHBOARD_HEADER_BACKGROUND_TOKEN = "ha-themes-dashboard-header-background"
"""Only the dashboard header blurs, but about a hundred other places paint
`app-header-background-color` without a blur, so that token stays opaque and the support
module paints the dashboard header with this one instead."""

TRANSLUCENT_SURFACES: dict[str, tuple[str, float]] = {
    DASHBOARD_HEADER_BACKGROUND_TOKEN: ("header_background", 0.72),
    "ha-card-background": ("surface", 0.8),
    "ha-dialog-surface-background": ("surface", 0.9),
}
"""A backdrop filter only shows through a translucent background, so each blurred element
also gets its role color with alpha."""

TYPOGRAPHY_BRIDGE: dict[str, str] = {
    "md-ref-typeface-plain": "var(--ha-font-family-body)",
    "mdc-typography-font-family": "var(--ha-font-family-body)",
}
"""Material components fall back to a literal Roboto instead of the HA body font."""

FORM_CONTROL_PADDING_FIX = {"wa-form-control-padding-inline": "var(--ha-space-3)"}
"""The frontend's dark styles glue the next stylesheet onto this value. Home Assistant keeps
that inline value after switching back to light, so both modes need it."""

UPSTREAM_FIXES: dict[str, dict[str, str]] = {
    "light": FORM_CONTROL_PADDING_FIX,
    "dark": {
        "ha-color-fill-neutral-quiet-active": "{neutral.05}",
        "ha-color-surface-lower-inverted": "{neutral.90}",
        "ha-color-border-primary-normal": "{primary.50}",
        **FORM_CONTROL_PADDING_FIX,
    },
}
"""Broken defaults of the captured frontend (see docs/theming-guide.md)."""

CONTRAST_PAIRS: tuple[tuple[str, str, float], ...] = (
    ("text", "background", 4.5),
    ("text", "surface", 4.5),
    ("text", "menu_background", 4.5),
    ("text_secondary", "surface", 4.5),
    ("text_on_primary", "primary", 4.5),
    ("text_on_primary", "primary_hover", 4.5),
    ("text_on_primary", "accent", 4.5),
    ("link", "surface", 4.5),
    ("primary", "surface", 3.0),
    ("error", "surface", 3.0),
)
