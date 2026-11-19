
from dataclasses import dataclass

from typing import TypeAlias

from .pen_event import PenEvent
from .scroll_event import ScrollEvent

DrawingEvent: TypeAlias = PenEvent | ScrollEvent


@dataclass(frozen=True)
class DrawingBatch:
    client_id: str
    sequence: int
    events: tuple[DrawingEvent, ...]
