
from dataclasses import dataclass



@dataclass(frozen=True)
class ScrollEvent:
    x: int
    y: int
