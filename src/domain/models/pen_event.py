from dataclasses import dataclass


from src.domain.enums.tool_state import ToolState


@dataclass(frozen=True)
class PenEvent:
    state: ToolState
    x: int
    y: int
    pressure: int
