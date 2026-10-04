"""CSS color values the validation can measure: hex in all four lengths and `rgb()`/`rgba()`.

Translucent colors only have a contrast once they are composited over an opaque backdrop, so
every measurement goes through `flatten` first. Named colors and color functions other than
`rgb()` do not parse; the checks report the pairs that use them as not evaluable.
"""

import re
from dataclasses import dataclass

from ha_theme_kit.color.oklch import contrast_ratio, rgb_to_hex

HEX_DIGITS = re.compile(r"#(?P<digits>[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})")
RGB_FUNCTION = re.compile(r"rgba?\((?P<arguments>[^()]*)\)", re.IGNORECASE)
NUMBER = r"[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?%?"
LEGACY_ARGUMENTS = re.compile(
    rf"\s*({NUMBER})\s*,\s*({NUMBER})\s*,\s*({NUMBER})\s*(?:,\s*({NUMBER})\s*)?", re.IGNORECASE
)
MODERN_ARGUMENTS = re.compile(
    rf"\s*({NUMBER})\s+({NUMBER})\s+({NUMBER})\s*(?:/\s*({NUMBER})\s*)?", re.IGNORECASE
)


@dataclass(frozen=True)
class CssColor:
    red: float
    green: float
    blue: float
    alpha: float = 1.0

    @property
    def is_opaque(self) -> bool:
        return self.alpha >= 1.0

    def over(self, backdrop: CssColor) -> CssColor:
        """Source-over compositing in gamma-encoded sRGB, as browsers paint it."""
        alpha = self.alpha + backdrop.alpha * (1 - self.alpha)
        if alpha == 0:
            return CssColor(0.0, 0.0, 0.0, 0.0)

        def blend(top: float, bottom: float) -> float:
            return (top * self.alpha + bottom * backdrop.alpha * (1 - self.alpha)) / alpha

        return CssColor(
            blend(self.red, backdrop.red),
            blend(self.green, backdrop.green),
            blend(self.blue, backdrop.blue),
            alpha,
        )

    def to_hex(self) -> str:
        return rgb_to_hex(self.red, self.green, self.blue)


def parse_css_color(value: str) -> CssColor | None:
    text = value.strip()
    if text.lower() == "transparent":
        return CssColor(0.0, 0.0, 0.0, 0.0)
    if hex_match := HEX_DIGITS.fullmatch(text):
        return _from_hex_digits(hex_match["digits"])
    if function_match := RGB_FUNCTION.fullmatch(text):
        return _from_rgb_arguments(function_match["arguments"])
    return None


def flatten(color: CssColor | None, backdrop: CssColor | None) -> CssColor | None:
    """`color` as it shows over `backdrop`, or None when either is unknown or the backdrop is
    itself translucent."""
    if color is None or color.is_opaque:
        return color
    if backdrop is None or not backdrop.is_opaque:
        return None
    return color.over(backdrop)


def contrast_on(foreground: CssColor | None, background: CssColor | None) -> float | None:
    """WCAG ratio of `foreground` painted on an opaque `background`, None when not evaluable."""
    if background is None or not background.is_opaque:
        return None
    painted = flatten(foreground, background)
    if painted is None:
        return None
    return round(contrast_ratio(painted.to_hex(), background.to_hex()), 2)


def _from_hex_digits(digits: str) -> CssColor:
    if len(digits) <= 4:
        digits = "".join(digit * 2 for digit in digits)
    channels = [int(digits[index : index + 2], 16) / 255 for index in range(0, len(digits), 2)]
    return CssColor(*channels)


def _from_rgb_arguments(arguments: str) -> CssColor | None:
    match = LEGACY_ARGUMENTS.fullmatch(arguments) or MODERN_ARGUMENTS.fullmatch(arguments)
    if match is None:
        return None
    red, green, blue, alpha = match.groups()
    return CssColor(
        _channel(red), _channel(green), _channel(blue), 1.0 if alpha is None else _alpha(alpha)
    )


def _channel(text: str) -> float:
    value = float(text[:-1]) / 100 if text.endswith("%") else float(text) / 255
    return min(max(value, 0.0), 1.0)


def _alpha(text: str) -> float:
    value = float(text[:-1]) / 100 if text.endswith("%") else float(text)
    return min(max(value, 0.0), 1.0)
