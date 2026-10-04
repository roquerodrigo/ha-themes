import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Oklch:
    lightness: float
    chroma: float
    hue: float


def hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    value = hex_color.lstrip("#")
    if len(value) == 3:
        value = "".join(character * 2 for character in value)
    if len(value) != 6:
        raise ValueError(f"Unsupported hex color: {hex_color}")
    return tuple(int(value[index : index + 2], 16) / 255 for index in (0, 2, 4))


def rgb_to_hex(red: float, green: float, blue: float) -> str:
    channels = (round(max(0.0, min(1.0, channel)) * 255) for channel in (red, green, blue))
    return "#" + "".join(f"{channel:02x}" for channel in channels)


def _to_linear(channel: float) -> float:
    if abs(channel) <= 0.04045:
        return channel / 12.92
    return math.copysign(((abs(channel) + 0.055) / 1.055) ** 2.4, channel)


def _to_gamma(channel: float) -> float:
    if abs(channel) <= 0.0031308:
        return channel * 12.92
    return math.copysign(1.055 * abs(channel) ** (1 / 2.4) - 0.055, channel)


def hex_to_oklch(hex_color: str) -> Oklch:
    red, green, blue = (_to_linear(channel) for channel in hex_to_rgb(hex_color))
    long_cone = math.cbrt(0.4122214708 * red + 0.5363325363 * green + 0.0514459929 * blue)
    medium_cone = math.cbrt(0.2119034982 * red + 0.6806995451 * green + 0.1073969566 * blue)
    short_cone = math.cbrt(0.0883024619 * red + 0.2817188376 * green + 0.6299787005 * blue)
    lightness = 0.2104542553 * long_cone + 0.7936177850 * medium_cone - 0.0040720468 * short_cone
    axis_a = 1.9779984951 * long_cone - 2.4285922050 * medium_cone + 0.4505937099 * short_cone
    axis_b = 0.0259040371 * long_cone + 0.7827717662 * medium_cone - 0.8086757660 * short_cone
    chroma = math.hypot(axis_a, axis_b)
    hue = math.degrees(math.atan2(axis_b, axis_a)) % 360
    return Oklch(lightness, chroma, hue)


def oklch_to_hex(color: Oklch) -> str:
    axis_a = color.chroma * math.cos(math.radians(color.hue))
    axis_b = color.chroma * math.sin(math.radians(color.hue))
    long_cone = (color.lightness + 0.3963377774 * axis_a + 0.2158037573 * axis_b) ** 3
    medium_cone = (color.lightness - 0.1055613458 * axis_a - 0.0638541728 * axis_b) ** 3
    short_cone = (color.lightness - 0.0894841775 * axis_a - 1.2914855480 * axis_b) ** 3
    red = 4.0767416621 * long_cone - 3.3077115913 * medium_cone + 0.2309699292 * short_cone
    green = -1.2684380046 * long_cone + 2.6097574011 * medium_cone - 0.3413193965 * short_cone
    blue = -0.0041960863 * long_cone - 0.7034186147 * medium_cone + 1.7076147010 * short_cone
    return rgb_to_hex(_to_gamma(red), _to_gamma(green), _to_gamma(blue))


def relative_luminance(hex_color: str) -> float:
    red, green, blue = (_to_linear(channel) for channel in hex_to_rgb(hex_color))
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(foreground: str, background: str) -> float:
    lighter, darker = sorted(
        (relative_luminance(foreground), relative_luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)
