"""Whether anything reads a token a role writes.

The catalog also lists tokens the frontend only declares in its default theme, so a role that
writes one of them passes validation while nobody sees its color.
"""

import re
from collections.abc import Iterable
from functools import cache

from ha_theme_kit.inventory.catalog import TokenCatalog
from ha_theme_kit.theme.roles import PROJECT_TOKEN_PREFIX, ROLE_TOKENS
from ha_theme_kit.theme.writer import render_support_module


@cache
def _support_module_source() -> str:
    return render_support_module()


def is_read_by_support_module(theme_key: str, support_source: str | None = None) -> bool:
    source = _support_module_source() if support_source is None else support_source
    return re.search(rf"--{re.escape(theme_key)}(?![\w-])", source) is not None


def has_reader(theme_key: str, catalog: TokenCatalog, support_source: str | None = None) -> bool:
    if theme_key.startswith(PROJECT_TOKEN_PREFIX):
        return is_read_by_support_module(theme_key, support_source)
    name = f"--{theme_key}"
    if any(name.startswith(prefix) for prefix in catalog.dynamic_families):
        return True
    entry = catalog.find(theme_key)
    return entry is not None and entry.consumers > 0


def unread_role_tokens(
    roles: Iterable[str], catalog: TokenCatalog, support_source: str | None = None
) -> list[str]:
    return sorted(
        {
            token
            for role in roles
            for token in ROLE_TOKENS[role]
            if not has_reader(token, catalog, support_source)
        }
    )
