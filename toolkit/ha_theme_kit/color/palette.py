from dataclasses import replace

from ha_theme_kit.color.oklch import hex_to_oklch, oklch_to_hex

PALETTE_STEPS = ("05", "10", "20", "30", "40", "50", "60", "70", "80", "90", "95")


def generate_tonal_scale(seed_color: str) -> dict[str, str]:
    """Port of the frontend's generateColorPalette: the seed sits at step 50."""
    seed = hex_to_oklch(seed_color)
    scale: dict[str, str] = {}
    for step_label in PALETTE_STEPS:
        step = int(step_label)
        if step == 50:
            scale[step_label] = oklch_to_hex(seed)
        elif step < 50:
            dark_factor = step / 50
            scale[step_label] = oklch_to_hex(
                replace(
                    seed,
                    lightness=seed.lightness * dark_factor,
                    chroma=seed.chroma * (0.9 + 0.1 * dark_factor),
                )
            )
        else:
            light_factor = (step - 50) / 45
            scale[step_label] = oklch_to_hex(
                replace(
                    seed,
                    lightness=min(1.0, seed.lightness + (1 - seed.lightness) * light_factor),
                    chroma=seed.chroma * max(0.0, 1 - light_factor * 0.7),
                )
            )
    return scale
