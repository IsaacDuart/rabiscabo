
from math import trunc

from src.domain.models import ScrollEvent
from .device import UInputDevice

WHEEL_CLICK = 120


class ScrollWheel:
    def __init__(self, device: UInputDevice):
        self._device = device
        self._remainder_x = 0
        self._remainder_y = 0

    def send(self, event: ScrollEvent) -> None:
        
        x, y = -event.x, event.y
        total_x = self._remainder_x + x
        total_y = self._remainder_y + y
        clicks_x = trunc(total_x / WHEEL_CLICK)
        clicks_y = trunc(total_y / WHEEL_CLICK)

        self._device.write_scroll(x, y, clicks_x, clicks_y)
        self._remainder_x = total_x - clicks_x * WHEEL_CLICK
        self._remainder_y = total_y - clicks_y * WHEEL_CLICK
