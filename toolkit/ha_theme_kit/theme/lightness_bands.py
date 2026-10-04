from ha_theme_kit.theme.modes import MODES


def parse_lightness_bands(section: str, document: dict | None) -> dict[str, tuple[float, float]]:
    bands = {}
    for mode, band in (document or {}).items():
        if mode not in MODES:
            raise ValueError(f"{section}.lightness has unknown mode {mode!r}")
        if not (
            isinstance(band, list | tuple)
            and len(band) == 2
            and all(_is_number(bound) for bound in band)
        ):
            raise ValueError(f"{section}.lightness.{mode} must be [minimum, maximum], got {band!r}")
        bands[mode] = (float(band[0]), float(band[1]))
    return bands


def _is_number(value: object) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)
