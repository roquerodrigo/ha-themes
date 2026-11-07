from typing import TYPE_CHECKING

from ha_theme_kit.color.css_color import CssColor, flatten
from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.token_colors import resolve_color_value, resolve_token_value

if TYPE_CHECKING:
    from ha_theme_kit.theme.builder import BuiltTheme

PAGE_ROLE = "background"
SURFACE_ROLE = "surface"


class ModeColors:
    """The roles and tokens of one mode as the colors they paint.

    The page has nothing under it, the surface sits on the page and every other role and token
    on the surface, so a translucent value is composited over that backdrop before it is
    measured.
    """

    def __init__(
        self, mode: str, roles: dict[str, str], tokens: dict[str, str], catalog: TokenCatalog
    ) -> None:
        self.mode = mode
        self.roles = roles
        self.tokens = tokens
        self.catalog = catalog

    @classmethod
    def of_theme(cls, theme: BuiltTheme, mode: str, catalog: TokenCatalog) -> ModeColors:
        return cls(mode, theme.roles[mode], theme.base | theme.modes[mode], catalog)

    def role(self, role: str) -> CssColor | None:
        value = self.roles.get(role)
        if value is None:
            return None
        return resolve_color_value(value, self.tokens, self.catalog, self.mode)

    def opaque_role(self, role: str) -> CssColor | None:
        color = self.role(role)
        if color is None or color.is_opaque or role == PAGE_ROLE:
            return flatten(color, None)
        return flatten(color, self.opaque_role(PAGE_ROLE if role == SURFACE_ROLE else SURFACE_ROLE))

    def token(self, key: str) -> CssColor | None:
        return resolve_token_value(key, self.tokens, self.catalog, self.mode)

    def opaque_token(self, key: str, backdrop_role: str | None = SURFACE_ROLE) -> CssColor | None:
        backdrop = None if backdrop_role is None else self.opaque_role(backdrop_role)
        return flatten(self.token(key), backdrop)
