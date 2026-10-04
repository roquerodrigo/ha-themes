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

from dataclasses import dataclass
from functools import cache

from ha_theme_kit.color.css_color import contrast_on
from ha_theme_kit.color.oklch import contrast_ratio
from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.loud_fills import DARK_ON_COLOR_STEP, ON_COLOR_CONTRAST_FLOOR, WHITE
from ha_theme_kit.theme.mode_colors import ModeColors
from ha_theme_kit.theme.tinted_on_colors import PALETTE_REFERENCE, contrast_floor, readable_on_color
from ha_theme_kit.theme.token_colors import resolve_token_color

TOAST_BACKGROUND_TOKEN = "ha-color-neutral-10"
TOAST_TEXT_TOKEN = "ha-themes-toast-text-color"
TOAST_ACTION_TOKEN = "ha-themes-toast-action-color"
FRONTEND_TEXT_TOKEN = "ha-color-on-neutral-loud"
FRONTEND_ACTION_TOKEN = "ha-color-on-primary-normal"
TOAST_ON_COLORS = {TOAST_TEXT_TOKEN: FRONTEND_TEXT_TOKEN, TOAST_ACTION_TOKEN: FRONTEND_ACTION_TOKEN}
"""Each toast token and the frontend on-color it replaces when unset."""


@dataclass(frozen=True)
class ToastPair:
    mode: str
    on_color_token: str
    ratio: float | None
    minimum: float

    @property
    def passes(self) -> bool:
        return self.ratio is not None and self.ratio >= self.minimum


def measure_toast_pairs(colors: ModeColors) -> list[ToastPair]:
    background = colors.opaque_token(TOAST_BACKGROUND_TOKEN, None)
    return [
        ToastPair(
            colors.mode,
            toast_token,
            contrast_on(
                colors.token(toast_token) or colors.token(frontend_token),
                background,
            ),
            contrast_floor(frontend_token, TOAST_BACKGROUND_TOKEN, colors.catalog, colors.mode),
        )
        for toast_token, frontend_token in TOAST_ON_COLORS.items()
    ]


def build_toast_colors(
    mode: str, tokens: dict[str, str], scales: dict[str, dict[str, str]]
) -> dict[str, str]:
    """Toast tokens only for the on-colors that miss their floor on the toast."""
    catalog = _frontend_catalog()
    background = resolve_token_color(TOAST_BACKGROUND_TOKEN, tokens, catalog, mode)
    if background is None:
        return {}
    toast_colors: dict[str, str] = {}
    text = resolve_token_color(FRONTEND_TEXT_TOKEN, tokens, catalog, mode)
    if text is None or _ratio(text, background) < ON_COLOR_CONTRAST_FLOOR:
        toast_colors[TOAST_TEXT_TOKEN] = max(
            (WHITE, scales["neutral"][DARK_ON_COLOR_STEP]),
            key=lambda candidate: _ratio(candidate, background),
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
    floor = contrast_floor(FRONTEND_ACTION_TOKEN, TOAST_BACKGROUND_TOKEN, catalog, mode)
    action = resolve_token_color(FRONTEND_ACTION_TOKEN, tokens, catalog, mode)
    if action is not None and _ratio(action, background) >= floor:
        return None
    entry = catalog.find(FRONTEND_ACTION_TOKEN)
    reference = entry and PALETTE_REFERENCE.fullmatch(
        (mode == "dark" and entry.dark) or entry.light or ""
    )
    if not reference:
        return None
    return readable_on_color(primary_scale, reference["step"], [(background, floor)])


def _ratio(foreground: str, background: str) -> float:
    return round(contrast_ratio(foreground, background), 2)


@cache
def _frontend_catalog() -> TokenCatalog:
    return TokenCatalog.load()
