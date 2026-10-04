from dataclasses import dataclass


@dataclass(frozen=True)
class ContrastResult:
    mode: str
    foreground_role: str
    background_role: str
    ratio: float | None
    """None when either side does not resolve to a color the check can measure."""
    minimum: float

    @property
    def passes(self) -> bool:
        return self.ratio is not None and self.ratio >= self.minimum
