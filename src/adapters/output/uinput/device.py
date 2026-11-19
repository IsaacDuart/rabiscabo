
from contextlib import ExitStack

from evdev import AbsInfo, UInput, ecodes
from evdev.uinput import UInputError

from src.config.settings import MAX_PRESSURE

DEVICE_PATH = "/dev/uinput"


def _open_device(name: str, product: int, events: dict) -> UInput:
    try:
        return UInput(
            events=events,
            name=name,
            vendor=0x0001,
            product=product,
            version=1,
            bustype=ecodes.BUS_VIRTUAL,
            devnode=DEVICE_PATH,
            input_props=[ecodes.INPUT_PROP_POINTER],
            max_effects=0,
        )
    except UInputError as error:
        raise RuntimeError(f"{error} Rode 'make setup' na sessão gráfica local.") from error
    except OSError as error:
        if error.filename is not None:
            raise
        raise OSError(error.errno, error.strerror, DEVICE_PATH) from error


class UInputDevice:
    def __init__(self, max_x: int, max_y: int):
        self._max_x = max_x
        self._max_y = max_y

    def __enter__(self) -> "UInputDevice":
        pen_events = {
            ecodes.EV_KEY: [ecodes.BTN_TOOL_PEN, ecodes.BTN_TOUCH],
            ecodes.EV_ABS: [
                (ecodes.ABS_X, AbsInfo(0, 0, self._max_x, 0, 0, 100)),
                (ecodes.ABS_Y, AbsInfo(0, 0, self._max_y, 0, 0, 100)),
                (ecodes.ABS_PRESSURE, AbsInfo(0, 0, MAX_PRESSURE, 0, 0, 0)),
            ],
        }
        scroll_events = {
            ecodes.EV_KEY: [ecodes.BTN_LEFT],
            ecodes.EV_REL: [
                ecodes.REL_X,
                ecodes.REL_Y,
                ecodes.REL_HWHEEL,
                ecodes.REL_HWHEEL_HI_RES,
                ecodes.REL_WHEEL,
                ecodes.REL_WHEEL_HI_RES,
            ],
        }
        with ExitStack() as devices:
            self._pen = devices.enter_context(_open_device("Mesa USB", 0x4D53, pen_events))
            self._scroll = devices.enter_context(
                _open_device("Mesa USB Rolagem", 0x4D54, scroll_events),
            )
            self._devices = devices.pop_all()
        return self

    def __exit__(self, *_):
        self._devices.close()

    def write_pen(self, x: int, y: int, pressure: int, in_range: bool, touching: bool) -> None:
        pen = self._pen
        pen.write(ecodes.EV_KEY, ecodes.BTN_TOUCH, int(touching))
        pen.write(ecodes.EV_KEY, ecodes.BTN_TOOL_PEN, int(in_range))
        pen.write(ecodes.EV_ABS, ecodes.ABS_X, x)
        pen.write(ecodes.EV_ABS, ecodes.ABS_Y, y)
        pen.write(ecodes.EV_ABS, ecodes.ABS_PRESSURE, pressure)
        pen.syn()

    def write_scroll(self, x: int, y: int, clicks_x: int, clicks_y: int) -> None:
        scroll = self._scroll
        scroll.write(ecodes.EV_REL, ecodes.REL_HWHEEL_HI_RES, x)
        scroll.write(ecodes.EV_REL, ecodes.REL_WHEEL_HI_RES, y)
        scroll.write(ecodes.EV_REL, ecodes.REL_HWHEEL, clicks_x)
        scroll.write(ecodes.EV_REL, ecodes.REL_WHEEL, clicks_y)
        scroll.syn()
