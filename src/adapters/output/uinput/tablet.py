
from src.domain.enums.tool_state import ToolState
from src.domain.models import DrawingEvent, PenEvent, ScrollEvent
from src.config.settings import MAX_COORDINATE

from .device import UInputDevice
from .scroll import ScrollWheel


class Tablet:
    def __init__(self, device: UInputDevice, max_x: int, max_y: int):
        self._device = device
        self._max_x = max_x
        self._max_y = max_y
        self._wheel = ScrollWheel(device)
        self._last = PenEvent(ToolState.OUT, 0, 0, 0)

    def send(self, event: DrawingEvent) -> None:
        if isinstance(event, ScrollEvent):
            self._wheel.send(event)
            return
        if event == self._last:
            return
        if {self._last.state, event.state} == {ToolState.OUT, ToolState.DOWN}:
            self._write_pen(PenEvent(ToolState.HOVER, event.x, event.y, 0))
        self._write_pen(event)
        self._last = event

    def release(self) -> None:
        self.send(PenEvent(ToolState.OUT, self._last.x, self._last.y, 0))

    def _write_pen(self, event: PenEvent) -> None:
        x = round(event.x * self._max_x / MAX_COORDINATE)
        y = round(event.y * self._max_y / MAX_COORDINATE)
        self._device.write_pen(
            x, y, event.pressure,
            event.state != ToolState.OUT,
            event.state == ToolState.DOWN,
        )
