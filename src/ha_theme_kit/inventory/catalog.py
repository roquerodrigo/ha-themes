import importlib.metadata
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from ha_theme_kit.inventory.browser_capture import RuntimeCapture
from ha_theme_kit.inventory.bundle_scan import BundleScan
from ha_theme_kit.inventory.classification import (
    classify_component_token,
    classify_global_token,
    is_private_token,
)

CATALOG_FILE = Path(__file__).resolve().parents[3] / "catalog" / "tokens.json"


@dataclass
class TokenEntry:
    name: str
    layer: str
    group: str
    light: str | None = None
    dark: str | None = None
    resolved_light: str | None = None
    resolved_dark: str | None = None
    reduced_motion: str | None = None
    consumers: int = 0
    fallbacks: list[str] = field(default_factory=list)

    @property
    def is_derived(self) -> bool:
        return bool(self.light and "var(" in self.light)

    @property
    def theme_key(self) -> str:
        return self.name.removeprefix("--")


@dataclass
class TokenCatalog:
    frontend_version: str
    core_version: str
    captured_at: str
    tokens: dict[str, TokenEntry]
    dynamic_families: dict[str, int] = field(default_factory=dict)

    def save(self, path: Path = CATALOG_FILE) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "frontend_version": self.frontend_version,
            "core_version": self.core_version,
            "captured_at": self.captured_at,
            "dynamic_families": self.dynamic_families,
            "tokens": [asdict(entry) for entry in sorted(self.tokens.values(), key=_sort_key)],
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

    @classmethod
    def load(cls, path: Path = CATALOG_FILE) -> TokenCatalog:
        payload = json.loads(path.read_text())
        tokens = {entry["name"]: TokenEntry(**entry) for entry in payload.pop("tokens")}
        return cls(tokens=tokens, **payload)

    def find(self, theme_key: str) -> TokenEntry | None:
        return self.tokens.get(f"--{theme_key.removeprefix('--')}")


def _sort_key(entry: TokenEntry) -> tuple[str, str, str]:
    return (entry.layer, entry.group, entry.name)


def build_catalog(runtime: RuntimeCapture, scan: BundleScan, frontend_version: str) -> TokenCatalog:
    tokens: dict[str, TokenEntry] = {}
    for name, light_value in runtime.light.declared.items():
        classification = classify_global_token(name)
        dark_value = runtime.dark.inline.get(name)
        tokens[name] = TokenEntry(
            name=name,
            layer=classification.layer,
            group=classification.group,
            light=light_value,
            dark=dark_value if dark_value not in (None, light_value) else None,
            resolved_light=runtime.light.computed.get(name),
            resolved_dark=runtime.dark.computed.get(name),
            reduced_motion=(runtime.light.conditional.get(name) or {}).get("value"),
        )
    for name, dark_value in runtime.dark.inline.items():
        if name not in tokens and not name.startswith("--rgb-"):
            classification = classify_global_token(name)
            tokens[name] = TokenEntry(
                name=name,
                layer=classification.layer,
                group=classification.group,
                dark=dark_value,
                resolved_dark=runtime.dark.computed.get(name),
            )
    for name, token_usage in scan.usage.items():
        if is_private_token(name):
            continue
        entry = tokens.get(name)
        if entry is None:
            classification = classify_component_token(name)
            entry = tokens[name] = TokenEntry(
                name=name, layer=classification.layer, group=classification.group
            )
            entry.fallbacks = sorted(token_usage.fallbacks)
        entry.consumers = len(token_usage.chunks)
    return TokenCatalog(
        frontend_version=frontend_version,
        core_version=importlib.metadata.version("homeassistant"),
        captured_at=datetime.now(UTC).date().isoformat(),
        tokens=tokens,
        dynamic_families=scan.dynamic_families,
    )
