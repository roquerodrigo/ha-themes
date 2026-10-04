import re

from ha_theme_kit.color.oklch import hex_to_rgba, is_opaque_hex
from ha_theme_kit.color.palette import PALETTE_STEPS, generate_tonal_scale

REQUIRED_FAMILIES = ("primary", "neutral", "red", "orange", "green")
FAMILY_NAME = re.compile(r"[a-z]+(?:-[a-z]+)*")
BRACED_TEXT = re.compile(r"\{[^{}]*\}")
REFERENCE = re.compile(
    rf"\{{(?P<family>{FAMILY_NAME.pattern})\.(?P<step>\d{{2}})(?:@(?P<alpha>\d*\.?\d+))?\}}"
)
REFERENCE_SYNTAX = "{family.step} or {family.step@alpha}"


class PaletteResolver:
    """Expands palette seeds into tonal scales and resolves `{family.step@alpha}` references."""

    def __init__(self, palette: dict[str, str | dict[str, str]]) -> None:
        missing = [family for family in REQUIRED_FAMILIES if family not in palette]
        if missing:
            raise ValueError(f"palette is missing families {missing}")
        invalid_names = sorted(
            str(family) for family in palette if not FAMILY_NAME.fullmatch(str(family))
        )
        if invalid_names:
            raise ValueError(
                f"palette family names {invalid_names} must be lowercase letters joined by hyphens"
            )
        self.scales = {family: self._expand(family, spec) for family, spec in palette.items()}

    @staticmethod
    def _expand(family: str, spec: str | dict[str, str]) -> dict[str, str]:
        if not isinstance(spec, dict):
            return generate_tonal_scale(_require_hex(f"palette.{family}", spec))
        explicit_steps = {
            str(step).zfill(2): value for step, value in spec.items() if step != "seed"
        }
        unknown_steps = sorted(set(explicit_steps) - set(PALETTE_STEPS))
        if unknown_steps:
            raise ValueError(
                f"palette family {family!r} has unknown steps {unknown_steps},"
                f" expected some of {list(PALETTE_STEPS)}"
            )
        for step, value in explicit_steps.items():
            _require_hex(f"palette.{family}.{step}", value)
        if "seed" in spec:
            seed = _require_hex(f"palette.{family}.seed", spec["seed"])
            return generate_tonal_scale(seed) | explicit_steps
        missing_steps = [step for step in PALETTE_STEPS if step not in explicit_steps]
        if missing_steps:
            raise ValueError(f"palette family {family!r} is missing steps {missing_steps}")
        return explicit_steps

    def core_tokens(self) -> dict[str, str]:
        return {
            f"ha-color-{family}-{step}": self.scales[family][step]
            for family in REQUIRED_FAMILIES
            for step in PALETTE_STEPS
        }

    def resolve(self, value: str, location: str) -> str:
        try:
            resolved = BRACED_TEXT.sub(self._replace_reference, value)
            if "{" in resolved or "}" in resolved:
                raise ValueError(f"unbalanced braces, expected {REFERENCE_SYNTAX}")
        except ValueError as error:
            raise ValueError(f"{location} {value!r}: {error}") from error
        return resolved

    def _replace_reference(self, braced: re.Match[str]) -> str:
        reference = braced.group(0)
        match = REFERENCE.fullmatch(reference)
        if match is None:
            raise ValueError(
                f"malformed palette reference {reference}, expected {REFERENCE_SYNTAX}"
            )
        family, step, alpha = match.group("family", "step", "alpha")
        if family not in self.scales:
            raise ValueError(f"unknown palette family in reference {reference}")
        if step not in self.scales[family]:
            raise ValueError(
                f"unknown palette step in reference {reference},"
                f" expected one of {list(PALETTE_STEPS)}"
            )
        color = self.scales[family][step]
        if alpha is None:
            return color
        if float(alpha) > 1:
            raise ValueError(f"alpha in reference {reference} must be between 0 and 1")
        return hex_to_rgba(color, alpha)


def _require_hex(path: str, value: object) -> str:
    if not isinstance(value, str) or not is_opaque_hex(value):
        raise ValueError(f"{path} must be an opaque hex color, got {value!r}")
    return value
