
from dataclasses import dataclass


@dataclass(frozen=True)
class DrawingArea:
    width: int
    height: int
