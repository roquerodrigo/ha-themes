from dataclasses import dataclass


@dataclass(frozen=True)
class ContrastResult:
    mode: str
    foreground_role: str
    background_role: str
    ratio: float | None
    """None when either side does not resolve to a color the check can measure."""
    minimum: float
    foreground_token: str | None = None
    background_token: str | None = None
    """The tokens behind a role pair's worst ratio, when the pair is measured on tokens."""

    @property
    def passes(self) -> bool:
        return self.ratio is not None and self.ratio >= self.minimum
