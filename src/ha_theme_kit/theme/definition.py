from dataclasses import dataclass, field
from pathlib import Path

import yaml

MODES = ("light", "dark")


@dataclass(frozen=True)
class ThemeDefinition:
    slug: str
    name: str
    description: str
    palette: dict[str, str | dict[str, str]]
    typography: dict[str, str] = field(default_factory=dict)
    roles: dict[str, dict[str, str]] = field(default_factory=dict)
    tokens: dict[str, dict[str, str]] = field(default_factory=dict)
    shadows: bool = False
    backdrop_blur: bool = True

    @classmethod
    def load(cls, path: Path) -> ThemeDefinition:
        document = yaml.safe_load(path.read_text())
        unknown_sections = set(document) - {
            "name",
            "description",
            "palette",
            "typography",
            "roles",
            "tokens",
            "shadows",
            "backdrop_blur",
        }
        if unknown_sections:
            raise ValueError(f"{path.name}: unknown sections {sorted(unknown_sections)}")
        for section in ("roles", "tokens"):
            unknown_modes = set(document.get(section) or {}) - {*MODES, "base"}
            if unknown_modes:
                raise ValueError(f"{path.name}: unknown {section} modes {sorted(unknown_modes)}")
        return cls(
            slug=path.stem,
            name=document["name"],
            description=document.get("description", ""),
            palette=document["palette"],
            typography=document.get("typography") or {},
            roles=document.get("roles") or {},
            tokens=document.get("tokens") or {},
            shadows=bool(document.get("shadows", False)),
            backdrop_blur=bool(document.get("backdrop_blur", True)),
        )
