"""Categorical palette checks: lightness band, chroma floor, color-vision-deficiency and
normal-vision separation (OKLab ΔE x100) and contrast against the surface.

Simulation uses Machado, Oliveira & Fernandes (2009) at severity 1.0 in linear RGB.
"""

import math
from dataclasses import dataclass
from itertools import pairwise

from ha_theme_kit.color.oklch import contrast_ratio, hex_to_oklch, hex_to_rgb

LIGHTNESS_BAND = {"light": (0.43, 0.77), "dark": (0.48, 0.67)}
CHROMA_FLOOR = 0.10
CVD_TARGET = 8.0
CVD_FLOOR = 6.0
NORMAL_VISION_FLOOR = 15.0
MARK_CONTRAST = 3.0

MACHADO_SIMULATIONS = {
    "protanopia": (
        (0.152286, 1.052583, -0.204868),
        (0.114503, 0.786281, 0.099216),
        (-0.003882, -0.048116, 1.051998),
    ),
    "deuteranopia": (
        (0.367322, 0.860646, -0.227968),
        (0.280085, 0.672501, 0.047413),
        (-0.011820, 0.042940, 0.968881),
    ),
}


def _linear_rgb(hex_color: str) -> tuple[float, float, float]:
    def to_linear(channel: float) -> float:
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4

    return tuple(to_linear(channel) for channel in hex_to_rgb(hex_color))


def _oklab(red: float, green: float, blue: float) -> tuple[float, float, float]:
    long_cone = math.cbrt(0.4122214708 * red + 0.5363325363 * green + 0.0514459929 * blue)
    medium_cone = math.cbrt(0.2119034982 * red + 0.6806995451 * green + 0.1073969566 * blue)
    short_cone = math.cbrt(0.0883024619 * red + 0.2817188376 * green + 0.6299787005 * blue)
    return (
        0.2104542553 * long_cone + 0.7936177850 * medium_cone - 0.0040720468 * short_cone,
        1.9779984951 * long_cone - 2.4285922050 * medium_cone + 0.4505937099 * short_cone,
        0.0259040371 * long_cone + 0.7827717662 * medium_cone - 0.8086757660 * short_cone,
    )


def _simulate(hex_color: str, deficiency: str | None) -> tuple[float, float, float]:
    linear = _linear_rgb(hex_color)
    if deficiency is None:
        return linear
    return tuple(
        max(
            0.0,
            min(1.0, sum(weight * channel for weight, channel in zip(row, linear, strict=True))),
        )
        for row in MACHADO_SIMULATIONS[deficiency]
    )


def color_distance(first: str, second: str, deficiency: str | None = None) -> float:
    return 100 * math.dist(
        _oklab(*_simulate(first, deficiency)), _oklab(*_simulate(second, deficiency))
    )


def worst_adjacent_cvd_distance(palette: list[str]) -> float:
    return min(
        color_distance(first, second, deficiency)
        for first, second in pairwise(palette)
        for deficiency in MACHADO_SIMULATIONS
    )


def worst_adjacent_normal_distance(palette: list[str]) -> float:
    return min(color_distance(first, second) for first, second in pairwise(palette))


@dataclass(frozen=True)
class CategoricalReport:
    mode: str
    outside_lightness_band: list[str]
    below_chroma_floor: list[str]
    worst_cvd_distance: float
    worst_normal_distance: float
    below_mark_contrast: list[str]

    @property
    def passes(self) -> bool:
        return (
            not self.outside_lightness_band
            and not self.below_chroma_floor
            and self.worst_cvd_distance >= CVD_FLOOR
            and self.worst_normal_distance >= NORMAL_VISION_FLOOR
        )


def check_categorical(palette: list[str], mode: str, surface: str) -> CategoricalReport:
    lower, upper = LIGHTNESS_BAND[mode]
    return CategoricalReport(
        mode=mode,
        outside_lightness_band=[
            color for color in palette if not lower <= hex_to_oklch(color).lightness <= upper
        ],
        below_chroma_floor=[
            color for color in palette if hex_to_oklch(color).chroma < CHROMA_FLOOR
        ],
        worst_cvd_distance=round(worst_adjacent_cvd_distance(palette), 1),
        worst_normal_distance=round(worst_adjacent_normal_distance(palette), 1),
        below_mark_contrast=[
            color for color in palette if contrast_ratio(color, surface) < MARK_CONTRAST
        ],
    )
