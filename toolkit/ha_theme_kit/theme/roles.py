"""Design roles a theme author decides on, and the frontend tokens each role drives.

Semantic `ha-color-*` tokens already derive from the core palette, so the roles below
cover what the palette cannot reach: application tokens the frontend hard-codes per mode.

`card-background-color` belongs to the page plane by design: the frontend paints it on
elements that sit directly on the page (data tables and their headers, the logbook's floating
date). Raised elements have their own hooks, mapped to `surface`: `ha-card-background`,
`ha-dialog-surface-background`, `wa-color-surface-default` and `mdc-theme-surface`. The
support module raises the elements that read `card-background-color` from a variable set on
their own host, out of a theme's reach: dropdown menus and the map overview panel take
`ha-themes-menu-background`, and the integration page's entry lists take `ha-card-background`.

`primary` and `text_on_primary` drive both the legacy pair (`primary-color` under
`text-primary-color`, also drawn on `accent-color`) and the loud fills of buttons and FABs,
so every filled primary element in a mode shows the same text color. `primary_light` is a
fill too: avatars, person badges and the Assist debug chat draw `text_on_primary_light` on it.

The code editor reads `code-editor-background-color` for itself, its completion popover and its
full-screen mode, falling back to `card-background-color`, the page plane. `code_editor_background`
follows `surface` instead, so all three read as raised like menus and the editor stays level with
the card it sits in. The `syntax_*` roles replace the frontend's off-palette CodeMirror colors
(Material Palenight in dark mode, CodeMirror's literals in light mode) and are validated against
that background: comments at 3:1, everything else at 4.5:1.
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
    "text_disabled": ("disabled-text-color",),
    "text_on_primary": ("text-primary-color", "ha-color-on-primary-loud"),
    "primary": (
        "primary-color",
        "ha-color-fill-primary-loud-resting",
        "ha-color-fill-primary-loud-active",
    ),
    "primary_hover": ("ha-color-fill-primary-loud-hover",),
    "primary_light": ("light-primary-color",),
    "text_on_primary_light": ("text-light-primary-color",),
    "primary_dark": ("dark-primary-color",),
    "accent": ("accent-color",),
    "divider": ("divider-color", "outline-color"),
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
    "sidebar_selected": ("sidebar-selected-icon-color",),
    "header_background": ("app-header-background-color",),
    "header_text": ("app-header-text-color",),
    "brand_icon": ("ha-themes-brand-icon-color",),
    "menu_background": ("ha-themes-menu-background",),
    "code_editor_background": ("code-editor-background-color",),
    "syntax_comment": ("codemirror-comment",),
    "syntax_keyword": ("codemirror-keyword",),
    "syntax_property": ("codemirror-property",),
    "syntax_string": ("codemirror-string", "codemirror-string2"),
    "syntax_number": ("codemirror-number", "codemirror-atom"),
    "syntax_variable": (
        "codemirror-variable",
        "codemirror-variable-2",
        "codemirror-qualifier",
        "codemirror-meta",
    ),
    "syntax_punctuation": ("codemirror-def", "codemirror-operator"),
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
        "text_on_primary_light": "{neutral.05}",
        "primary_dark": "{primary.30}",
        "accent": "{orange.60}",
        "divider": "{neutral.05@0.12}",
        "error": "{red.40}",
        "warning": "{orange.40}",
        "success": "{green.40}",
        "info": "{primary.40}",
        "scrollbar": "{neutral.70}",
        "shadow": "rgba(0, 0, 0, 0.16)",
        "input_fill": "{neutral.95}",
        "code_background": "{neutral.95}",
        "syntax_comment": "{neutral.50}",
        "syntax_keyword": "{primary.30}",
        "syntax_property": "{neutral.20}",
        "syntax_string": "{green.40}",
        "syntax_number": "{orange.30}",
        "syntax_variable": "{neutral.20}",
        "syntax_punctuation": "{neutral.40}",
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
        "text_on_primary_light": "{neutral.95}",
        "primary_dark": "{primary.60}",
        "accent": "{orange.60}",
        "divider": "{neutral.90@0.12}",
        "error": "{red.70}",
        "warning": "{orange.60}",
        "success": "{green.60}",
        "info": "{primary.60}",
        "scrollbar": "{neutral.60}",
        "shadow": "rgba(0, 0, 0, 0.48)",
        "input_fill": "{neutral.90@0.05}",
        "code_background": "{neutral.05}",
        "syntax_comment": "{neutral.60}",
        "syntax_keyword": "{primary.60}",
        "syntax_property": "{neutral.80}",
        "syntax_string": "{green.60}",
        "syntax_number": "{orange.60}",
        "syntax_variable": "{neutral.80}",
        "syntax_punctuation": "{neutral.70}",
    },
}

ROLE_FALLBACKS: dict[str, str] = {
    "sidebar_background": "background",
    "header_background": "background",
    "brand_icon": "primary",
    "state_icon": "primary",
    "menu_background": "surface",
    "code_editor_background": "surface",
}
"""Roles that follow another role unless a theme sets them: chrome blends into the page,
generic integration icons and entity icons without a state color take the primary color, and
menus and the code editor are raised like cards."""

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
)
"""A transparent zero shadow instead of `none` stays valid inside comma-separated shadow lists."""

TOAST_EDGE_TOKEN = "ha-themes-toast-box-shadow"
"""The toast reads the shared `wa-shadow-l` directly, so the support module paints its edge
with this token instead."""

OVERLAY_EDGE: dict[str, str] = dict.fromkeys(
    ("ha-tooltip-box-shadow", TOAST_EDGE_TOKEN), "0 0 0 1px var(--outline-color)"
)
"""Tooltips and toasts float over the page with only a shadow to separate them, so flat
elevation gives them the 1px outline that menus and cards already have."""

ICON_TILE_HARMONY: dict[str, str] = {
    "ha-themes-icon-tile-palette-share": "100%",
    "ha-themes-icon-tile-max-lightness": "0.6",
}
"""Settings, System, About and the search dialog draw their icon tiles in literal colors. The
support module moves each tile to the entity color of the same hue by this share, and caps its
OKLCH lightness so the white glyph keeps about 4:1 in both modes."""

FIELD_OUTLINE: dict[str, str] = {
    "ha-themes-field-outline": "1",
    "ha-themes-field-border-color": "var(--ha-color-border-neutral-quiet)",
    "ha-themes-field-border-radius": "var(--ha-border-radius-md)",
}
"""Filled text fields, selects and pickers mark their edge with a bottom line. The support
module outlines them instead, takes the focus and error colors over to the outline, hides the
line and clears the fill."""

CORNER_RADIUS_TOKEN = "ha-themes-corner-radius"
"""Read by the support module where a component locks a literal radius on its own host."""

CORNER_RADIUS_SCALE: tuple[str, ...] = (
    "ha-border-radius-xs",
    "ha-border-radius-s",
    "ha-border-radius-small",
    "ha-border-radius-sm",
    "ha-border-radius-md",
    "ha-border-radius-lg",
    "ha-border-radius-xl",
    "ha-border-radius-2xl",
    "ha-border-radius-3xl",
    "ha-border-radius-4xl",
    "ha-border-radius-5xl",
    "ha-border-radius-6xl",
    "ha-border-radius-pill",
)
"""The frontend's radius scale, plus the three names components read but it never declares.
`ha-border-radius-square` and `ha-border-radius-circle` are shapes, not sizes, and stay."""

CORNER_RADIUS_BRIDGES: tuple[str, ...] = (
    "wa-border-radius-s",
    "wa-border-radius-m",
    "wa-border-radius-l",
    "wa-border-radius-pill",
    "wa-form-control-border-radius",
    "wa-panel-border-radius",
    "mdc-shape-small",
    "mdc-shape-medium",
    "mdc-shape-large",
    "ha-assist-chip-container-shape",
    "ha-card-border-radius",
    "ha-card-features-border-radius",
    "ha-dialog-border-radius",
    "ha-bottom-sheet-border-radius",
    "ha-section-border-radius",
    "ha-button-border-radius",
    "ha-badge-border-radius",
    "ha-heading-badge-border-radius",
    "ha-tile-icon-border-radius",
    "ha-favorite-color-button-border-radius",
    "ha-tooltip-border-radius",
    "ha-input-search-border-radius",
    "ha-checkbox-border-radius",
    "ha-bar-border-radius",
    "ha-progress-bar-border-radius",
    "calendar-border-radius",
    "markdown-image-border-radius",
)
"""Component and library radii that fall back to a literal or to a fixed step of the scale
instead of following it, so the scale alone would not reach them."""

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
    ("text_secondary", "background", 4.5),
    ("text_secondary", "surface", 4.5),
    ("text_on_primary", "primary", 4.5),
    ("text_on_primary", "primary_hover", 4.5),
    ("text_on_primary", "accent", 4.5),
    ("text_on_primary_light", "primary_light", 4.5),
    ("primary", "background", 3.0),
    ("primary", "surface", 3.0),
    ("state_icon", "background", 3.0),
    ("state_icon", "surface", 3.0),
    ("error", "background", 4.5),
    ("error", "surface", 4.5),
    ("warning", "background", 4.5),
    ("warning", "surface", 4.5),
    ("success", "background", 4.5),
    ("success", "surface", 4.5),
    ("info", "background", 4.5),
    ("info", "surface", 4.5),
    ("text", "code_editor_background", 4.5),
    ("syntax_comment", "code_editor_background", 3.0),
    ("syntax_keyword", "code_editor_background", 4.5),
    ("syntax_property", "code_editor_background", 4.5),
    ("syntax_string", "code_editor_background", 4.5),
    ("syntax_number", "code_editor_background", 4.5),
    ("syntax_variable", "code_editor_background", 4.5),
    ("syntax_punctuation", "code_editor_background", 4.5),
)
"""Text pairs need 4.5:1 and graphical ones 3:1. The status colors and secondary text are drawn
as text (log levels, error messages, captions). `primary` also colors links, but it is the brand
fill of buttons, badges and switches, so the builder never moves it and it is held to the 3:1 of
a graphical part, as is `state_icon`, the default color of entity icons; buttons draw their text
in the normal primary on-color, checked at 4.5:1."""
