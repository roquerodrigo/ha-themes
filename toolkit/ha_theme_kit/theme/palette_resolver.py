import re

from ha_theme_kit.color.oklch import hex_to_rgba
from ha_theme_kit.color.palette import PALETTE_STEPS, generate_tonal_scale

REQUIRED_FAMILIES = ("primary", "neutral", "red", "orange", "green")
REFERENCE = re.compile(r"\{(?P<family>[a-z]+)\.(?P<step>\d{2})(?:@(?P<alpha>[0-9.]+))?\}")


class PaletteResolver:
    """Expands palette seeds into tonal scales and resolves `{family.step@alpha}` references."""

    def __init__(self, palette: dict[str, str | dict[str, str]]) -> None:
        missing = [family for family in REQUIRED_FAMILIES if family not in palette]
        if missing:
            raise ValueError(f"palette is missing families {missing}")
        self.scales = {family: self._expand(family, spec) for family, spec in palette.items()}

    @staticmethod
    def _expand(family: str, spec: str | dict[str, str]) -> dict[str, str]:
        if isinstance(spec, str):
            return generate_tonal_scale(spec)
        if "seed" in spec:
            scale = generate_tonal_scale(spec["seed"])
            scale.update(
                {str(step).zfill(2): value for step, value in spec.items() if step != "seed"}
            )
            return scale
        scale = {str(step).zfill(2): value for step, value in spec.items()}
        missing_steps = [step for step in PALETTE_STEPS if step not in scale]
        if missing_steps:
            raise ValueError(f"palette family {family!r} is missing steps {missing_steps}")
        return scale

    def core_tokens(self) -> dict[str, str]:
        return {
            f"ha-color-{family}-{step}": self.scales[family][step]
            for family in REQUIRED_FAMILIES
            for step in PALETTE_STEPS
        }

    def resolve(self, value: str) -> str:
        return REFERENCE.sub(self._replace_reference, value)

    def _replace_reference(self, match: re.Match[str]) -> str:
        family, step, alpha = match.group("family", "step", "alpha")
        if family not in self.scales:
            raise ValueError(f"unknown palette family in reference {match.group(0)}")
        color = self.scales[family][step]
        if alpha is None:
            return color
        return hex_to_rgba(color, alpha)
