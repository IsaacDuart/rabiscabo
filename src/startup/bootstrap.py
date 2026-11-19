
import signal
from functools import partial
from threading import Event

from src.adapters.input.http.server import serve_local
from src.adapters.output.adb.devices import AdbDevices
from src.application.receiver import Receiver
from src.domain.models.area import DrawingArea


def run(area: DrawingArea) -> None:
    from src.adapters.output.uinput.device import UInputDevice
    from src.adapters.output.uinput.tablet import Tablet

    stopped = Event()

    def stop(*_):
        stopped.set()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    max_x, max_y = area.width * 100, area.height * 100
    receiver = Receiver(AdbDevices(), serve_local, partial(print, flush=True))
    with UInputDevice(max_x, max_y) as device:
        receiver.run(Tablet(device, max_x, max_y), area, stopped)
