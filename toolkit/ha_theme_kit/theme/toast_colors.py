"""Toast message and action colors that stay readable on the toast.

The frontend paints every toast in `ha-color-neutral-10`, in both modes, with
`ha-color-on-neutral-loud` for the message and plain primary buttons, drawn in
`ha-color-on-primary-normal`, for the actions. Both on-colors are tuned for other backdrops: a
theme whose loud neutral fill is a light grey in dark mode takes dark text there, which then
lands on the dark toast, and the normal primary text is tuned for the page. The support module
paints the toast with its own two tokens, which the builder sets only where the frontend's
on-colors miss the floor: the message takes white or the darkest neutral, and the action the
nearest primary step that reads.
"""

from ha_theme_kit.color.css_color import contrast_on
from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.contrast_result import ContrastResult
from ha_theme_kit.theme.loud_fills import DARK_ON_COLOR_STEP, WHITE
from ha_theme_kit.theme.mode_colors import ModeColors
from ha_theme_kit.theme.semantic_layer import (
    TEXT_CONTRAST_FLOOR,
    frontend_catalog,
    frontend_floor,
    frontend_palette_step,
    nearest_readable_step,
    rounded_ratio,
)
from ha_theme_kit.theme.token_colors import resolve_token_color

TOAST_BACKGROUND_TOKEN = "ha-color-neutral-10"
TOAST_TEXT_TOKEN = "ha-themes-toast-text-color"
TOAST_ACTION_TOKEN = "ha-themes-toast-action-color"
FRONTEND_TEXT_TOKEN = "ha-color-on-neutral-loud"
FRONTEND_ACTION_TOKEN = "ha-color-on-primary-normal"
TOAST_ON_COLORS = {TOAST_TEXT_TOKEN: FRONTEND_TEXT_TOKEN, TOAST_ACTION_TOKEN: FRONTEND_ACTION_TOKEN}
"""Each toast token and the frontend on-color it replaces when unset."""


def measure_toast_pairs(colors: ModeColors) -> list[ContrastResult]:
    background = colors.opaque_token(TOAST_BACKGROUND_TOKEN, None)
    return [
        ContrastResult(
            colors.mode,
            toast_token,
            TOAST_BACKGROUND_TOKEN,
            contrast_on(colors.token(toast_token) or colors.token(frontend_token), background),
            _floor(frontend_token, colors.catalog, colors.mode),
        )
        for toast_token, frontend_token in TOAST_ON_COLORS.items()
    ]


def build_toast_colors(
    mode: str, tokens: dict[str, str], scales: dict[str, dict[str, str]]
) -> dict[str, str]:
    """Toast tokens only for the on-colors that miss their floor on the toast."""
    catalog = frontend_catalog()
    background = resolve_token_color(TOAST_BACKGROUND_TOKEN, tokens, catalog, mode)
    if background is None:
        return {}
    toast_colors: dict[str, str] = {}
    text = resolve_token_color(FRONTEND_TEXT_TOKEN, tokens, catalog, mode)
    if text is None or rounded_ratio(text, background) < TEXT_CONTRAST_FLOOR:
        toast_colors[TOAST_TEXT_TOKEN] = max(
            (WHITE, scales["neutral"][DARK_ON_COLOR_STEP]),
            key=lambda candidate: rounded_ratio(candidate, background),
        )
    action = _readable_action(mode, tokens, scales["primary"], background, catalog)
    if action is not None:
        toast_colors[TOAST_ACTION_TOKEN] = action
    return toast_colors


def _readable_action(
    mode: str,
    tokens: dict[str, str],
    primary_scale: dict[str, str],
    background: str,
    catalog: TokenCatalog,
) -> str | None:
    """The primary step nearest the frontend's that reads on the toast, None if that one does."""
    floor = _floor(FRONTEND_ACTION_TOKEN, catalog, mode)
    action = resolve_token_color(FRONTEND_ACTION_TOKEN, tokens, catalog, mode)
    if action is not None and rounded_ratio(action, background) >= floor:
        return None
    step = frontend_palette_step(FRONTEND_ACTION_TOKEN, catalog, mode)
    if step is None:
        return None
    return nearest_readable_step(primary_scale, step[1], [(background, floor)])


def _floor(frontend_token: str, catalog: TokenCatalog, mode: str) -> float:
    return frontend_floor(
        frontend_token, TOAST_BACKGROUND_TOKEN, TEXT_CONTRAST_FLOOR, catalog, mode
    )
