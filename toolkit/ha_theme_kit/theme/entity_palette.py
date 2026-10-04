"""Entity colors: the frontend's named colors, which every `state-*` color references.

Each hue keeps the meaning Home Assistant gives it (amber for lights on, green for locked,
red for alarms) and is restyled per mode: chroma capped to the theme's mood, lightness
clamped into a band that reads on that mode's surfaces.
"""

from dataclasses import dataclass, field

from ha_theme_kit.color.oklch import restyle
from ha_theme_kit.theme.palette_resolver import PaletteResolver

FRONTEND_NAMED_HUES = {
    "red": "#f44336",
    "pink": "#e91e63",
    "purple": "#926bc7",
    "deep-purple": "#6e41ab",
    "indigo": "#3f51b5",
    "blue": "#2196f3",
    "light-blue": "#03a9f4",
    "cyan": "#00bcd4",
    "teal": "#009688",
    "green": "#4caf50",
    "light-green": "#8bc34a",
    "lime": "#cddc39",
    "yellow": "#ffeb3b",
    "amber": "#ffc107",
    "orange": "#ff9800",
    "deep-orange": "#ff6f22",
    "brown": "#795548",
    "blue-grey": "#607d8b",
}
"""Light defaults of frontend 20260826.7; a test keeps them in sync with the catalog."""

NEUTRAL_NAMES = {
    "light": {
        "light-grey": "{neutral.70}",
        "grey": "{neutral.60}",
        "dark-grey": "{neutral.40}",
        "disabled": "{neutral.80}",
    },
    "dark": {
        "light-grey": "{neutral.70}",
        "grey": "{neutral.60}",
        "dark-grey": "{neutral.50}",
        "disabled": "{neutral.30}",
    },
}

ENERGY_COLORS = {
    "energy-grid-consumption-color": "blue",
    "energy-grid-return-color": "purple",
    "energy-solar-color": "orange",
    "energy-non-fossil-color": "green",
    "energy-battery-out-color": "teal",
    "energy-battery-in-color": "pink",
    "energy-gas-color": "red",
    "energy-water-color": "cyan",
}

WEATHER_ICON_COLORS = {
    "weather-icon-sun-color": "amber",
    "weather-icon-moon-color": "yellow",
    "weather-icon-rain-color": "light-blue",
}
WEATHER_ICON_NEUTRALS = {
    "light": {
        "weather-icon-cloud-front-color": "{neutral.90}",
        "weather-icon-cloud-back-color": "{neutral.80}",
        "weather-icon-snow-color": "{neutral.95}",
        "weather-icon-snow-stroke-color": "{neutral.70}",
    },
    "dark": {
        "weather-icon-cloud-front-color": "{neutral.80}",
        "weather-icon-cloud-back-color": "{neutral.60}",
        "weather-icon-snow-color": "{neutral.95}",
        "weather-icon-snow-stroke-color": "{neutral.60}",
    },
}


@dataclass(frozen=True)
class EntityColorSettings:
    chroma_cap: float = 0.16
    lightness: dict[str, tuple[float, float]] = field(
        default_factory=lambda: {"light": (0.50, 0.80), "dark": (0.62, 0.86)}
    )
    pinned: dict[str, str | dict[str, str]] = field(default_factory=dict)

    @classmethod
    def from_document(cls, document: dict | None) -> EntityColorSettings:
        if not document:
            return cls()
        defaults = cls()
        lightness = {mode: tuple(band) for mode, band in (document.get("lightness") or {}).items()}
        unknown = (
            set(document.get("pinned") or {})
            - set(FRONTEND_NAMED_HUES)
            - set(NEUTRAL_NAMES["light"])
        )
        if unknown:
            raise ValueError(f"entity_colors.pinned has unknown colors {sorted(unknown)}")
        return cls(
            chroma_cap=float(document.get("chroma_cap", defaults.chroma_cap)),
            lightness={**defaults.lightness, **lightness},
            pinned=document.get("pinned") or {},
        )


def build_entity_colors(
    settings: EntityColorSettings, resolver: PaletteResolver, mode: str
) -> dict[str, str]:
    colors = {
        name: restyle(default, settings.lightness[mode], (0.0, settings.chroma_cap))
        for name, default in FRONTEND_NAMED_HUES.items()
    }
    colors |= {name: resolver.resolve(value) for name, value in NEUTRAL_NAMES[mode].items()}
    for name, value in settings.pinned.items():
        colors[name] = resolver.resolve(value[mode] if isinstance(value, dict) else value)
    tokens = {f"{name}-color": color for name, color in colors.items()}
    tokens |= {token: colors[name] for token, name in ENERGY_COLORS.items()}
    tokens |= {token: colors[name] for token, name in WEATHER_ICON_COLORS.items()}
    tokens |= {
        token: resolver.resolve(value) for token, value in WEATHER_ICON_NEUTRALS[mode].items()
    }
    return tokens
