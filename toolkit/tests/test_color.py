import pytest

from ha_theme_kit.color.oklch import contrast_ratio, hex_to_oklch, oklch_to_hex
from ha_theme_kit.color.palette import generate_tonal_scale

CULORI_REFERENCE_SCALES = {
    "#d97757": "#130000 #280000 #520000 #7e2805 #ab4f31 #d97757 "
    "#e89378 #f7b099 #ffccba #ffe9db #fff7ec",
    "#6a9bcc": "#000016 #000528 #00274d #1e4b75 #4472a0 #6a9bcc "
    "#88b1dc #a5c8eb #c4dffa #e2f6ff #f2ffff",
    "#009ac7": "#000019 #00062a #00294e #004d74 #00739d #009ac7 "
    "#53b2d8 #80c9e9 #aae1fa #d2f9ff #e6ffff",
}


@pytest.mark.parametrize(("seed", "expected"), CULORI_REFERENCE_SCALES.items())
def test_tonal_scale_matches_frontend_algorithm(seed: str, expected: str) -> None:
    assert " ".join(generate_tonal_scale(seed).values()) == expected


@pytest.mark.parametrize("color", ["#000000", "#ffffff", "#d97757", "#141413", "#6a9bcc"])
def test_oklch_round_trip(color: str) -> None:
    assert oklch_to_hex(hex_to_oklch(color)) == color


def test_contrast_ratio_extremes() -> None:
    assert contrast_ratio("#000000", "#ffffff") == pytest.approx(21.0)
    assert contrast_ratio("#777777", "#777777") == pytest.approx(1.0)
