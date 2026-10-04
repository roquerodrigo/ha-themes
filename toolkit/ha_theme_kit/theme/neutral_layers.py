"""Neutral fills the frontend layers over the page and the surface.

The frontend points form fields, the quiet and normal neutral fills and `ha-color-surface-low`
at fixed steps of the neutral scale, chosen for its own page and surface. A theme that moves
its page or surface along the scale would leave fields level with the surface and hover fills
darker than it. For each role that moved, the builder keeps the frontend's OKLCH lightness
offset from that role and takes the color at the new lightness from the theme's own neutral
scale, so the fills keep the theme's hue.
"""

from dataclasses import dataclass
from itertools import pairwise

from ha_theme_kit.color.oklch import hex_to_oklch, is_opaque_hex, mix
from ha_theme_kit.color.vision import color_distance

FORM_BACKGROUND = "ha-color-form-background"
FORM_BACKGROUND_HOVER = "ha-color-form-background-hover"
FORM_BACKGROUND_DISABLED = "ha-color-form-background-disabled"
QUIET_RESTING = "ha-color-fill-neutral-quiet-resting"
QUIET_HOVER = "ha-color-fill-neutral-quiet-hover"
QUIET_ACTIVE = "ha-color-fill-neutral-quiet-active"
NORMAL_RESTING = "ha-color-fill-neutral-normal-resting"
NORMAL_HOVER = "ha-color-fill-neutral-normal-hover"
NORMAL_ACTIVE = "ha-color-fill-neutral-normal-active"
SURFACE_LOW = "ha-color-surface-low"

FRONTEND_NEUTRALS: dict[str, str] = {
    "05": "#141414",
    "10": "#202020",
    "20": "#363636",
    "30": "#4a4a4a",
    "80": "#cccccc",
    "90": "#e6e6e6",
    "95": "#f3f3f3",
}
"""The frontend's own neutral steps that the layered tokens reference."""

MOVED_ROLE_DISTANCE = 2.0
"""OKLab ΔE from the frontend's page or surface past which a theme's role counts as moved."""

DISABLED_FIELD_SHARE = 0.5
"""Dark mode paints disabled fields like enabled ones; halfway to the surface keeps them
recognizable as fields while reading as inactive."""


@dataclass(frozen=True)
class FrontendLayering:
    anchors: dict[str, str]
    steps: dict[str, tuple[str, str]]


FRONTEND_LAYERING: dict[str, FrontendLayering] = {
    "light": FrontendLayering(
        anchors={"background": "#fafafa", "surface": "#ffffff"},
        steps={
            FORM_BACKGROUND: ("surface", "95"),
            FORM_BACKGROUND_HOVER: ("surface", "90"),
            FORM_BACKGROUND_DISABLED: ("surface", "80"),
            QUIET_RESTING: ("background", "95"),
            QUIET_HOVER: ("surface", "90"),
            QUIET_ACTIVE: ("background", "95"),
            NORMAL_RESTING: ("surface", "90"),
            NORMAL_HOVER: ("surface", "80"),
            NORMAL_ACTIVE: ("surface", "90"),
            SURFACE_LOW: ("background", "95"),
        },
    ),
    "dark": FrontendLayering(
        anchors={"background": "#111111", "surface": "#1c1c1c"},
        steps={
            FORM_BACKGROUND: ("surface", "20"),
            FORM_BACKGROUND_HOVER: ("surface", "30"),
            FORM_BACKGROUND_DISABLED: ("surface", "20"),
            QUIET_RESTING: ("background", "05"),
            QUIET_HOVER: ("surface", "10"),
            QUIET_ACTIVE: ("background", "05"),
            NORMAL_RESTING: ("surface", "10"),
            NORMAL_HOVER: ("surface", "20"),
            NORMAL_ACTIVE: ("surface", "10"),
            SURFACE_LOW: ("background", "05"),
        },
    ),
}
"""Per mode, the frontend's page and raised surface (cards and dialogs read
`card-background-color`), and for each token the role it is drawn on and the neutral step the
frontend gives it. Dark quiet-active points at a missing step upstream; `05` is the step the
builder repairs it to."""


def layer_neutral_fills(
    mode: str, roles: dict[str, str], neutral_scale: dict[str, str]
) -> dict[str, str]:
    layering = FRONTEND_LAYERING[mode]
    moved_roles = {
        role
        for role, frontend_color in layering.anchors.items()
        if is_opaque_hex(roles[role])
        and color_distance(roles[role], frontend_color) >= MOVED_ROLE_DISTANCE
    }
    ladder = _lightness_ladder(neutral_scale)
    fills = {
        token: _offset_from(roles[role], layering.anchors[role], FRONTEND_NEUTRALS[step], ladder)
        for token, (role, step) in layering.steps.items()
        if role in moved_roles
    }
    enabled_step = layering.steps[FORM_BACKGROUND][1]
    if layering.steps[FORM_BACKGROUND_DISABLED][1] == enabled_step and is_opaque_hex(
        roles["surface"]
    ):
        enabled = fills.get(FORM_BACKGROUND, neutral_scale[enabled_step])
        fills[FORM_BACKGROUND_DISABLED] = mix(roles["surface"], enabled, DISABLED_FIELD_SHARE)
    return fills


def _lightness_ladder(neutral_scale: dict[str, str]) -> list[tuple[float, str]]:
    colors = [*neutral_scale.values(), "#000000", "#ffffff"]
    return sorted((hex_to_oklch(color).lightness, color) for color in colors)


def _offset_from(
    theme_anchor: str, frontend_anchor: str, frontend_color: str, ladder: list[tuple[float, str]]
) -> str:
    offset = hex_to_oklch(frontend_color).lightness - hex_to_oklch(frontend_anchor).lightness
    target = hex_to_oklch(theme_anchor).lightness + offset
    for (lower_lightness, lower), (upper_lightness, upper) in pairwise(ladder):
        if target <= upper_lightness and upper_lightness > lower_lightness:
            share = max(0.0, target - lower_lightness) / (upper_lightness - lower_lightness)
            return mix(lower, upper, share)
    return ladder[-1][1]
