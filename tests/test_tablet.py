import errno
import unittest
from unittest.mock import MagicMock, call, patch

from evdev import UInput, ecodes

from src.adapters.output.uinput.device import UInputDevice
from src.adapters.output.uinput.tablet import Tablet
from src.domain.enums.tool_state import ToolState
from src.domain.models import PenEvent, ScrollEvent


class TabletTests(unittest.TestCase):
    def setUp(self):
        self.pen = MagicMock(spec=UInput)
        self.pen.__enter__.return_value = self.pen
        self.scroll = MagicMock(spec=UInput)
        self.scroll.__enter__.return_value = self.scroll

        factory = patch(
            "src.adapters.output.uinput.device.UInput",
            side_effect=[self.pen, self.scroll],
        )
        self.factory = factory.start()
        self.addCleanup(factory.stop)

    def test_tap_includes_proximity_before_and_after_contact(self):
        with UInputDevice(24000, 13500) as device:
            tablet = Tablet(device, 24000, 13500)
            tablet.send(PenEvent(ToolState.DOWN, 32768, 65535, 4095))
            tablet.release()

        expected_frames = []
        for touching, in_range, pressure in [(0, 1, 0), (1, 1, 4095), (0, 1, 0), (0, 0, 0)]:
            expected_frames.extend([
                call.write(ecodes.EV_KEY, ecodes.BTN_TOUCH, touching),
                call.write(ecodes.EV_KEY, ecodes.BTN_TOOL_PEN, in_range),
                call.write(ecodes.EV_ABS, ecodes.ABS_X, 12000),
                call.write(ecodes.EV_ABS, ecodes.ABS_Y, 13500),
                call.write(ecodes.EV_ABS, ecodes.ABS_PRESSURE, pressure),
                call.syn(),
            ])
        self.assertEqual(self.pen.method_calls, expected_frames)
        self.pen.__exit__.assert_called_once()
        self.scroll.__exit__.assert_called_once()

        pen_options = self.factory.call_args_list[0].kwargs
        axes = dict(pen_options["events"][ecodes.EV_ABS])
        self.assertEqual((axes[ecodes.ABS_X].max, axes[ecodes.ABS_Y].max), (24000, 13500))
        self.assertEqual(axes[ecodes.ABS_X].resolution, 100)
        self.assertEqual(axes[ecodes.ABS_PRESSURE].max, 4095)
        self.assertEqual(pen_options["input_props"], [ecodes.INPUT_PROP_POINTER])

    def test_scroll_accumulates_wheel_detents(self):
        with UInputDevice(24000, 13500) as device:
            tablet = Tablet(device, 24000, 13500)
            tablet.send(ScrollEvent(70, -80))
            tablet.send(ScrollEvent(70, -80))

        expected_frames = []
        for clicks in (0, -1):
            expected_frames.extend([
                call.write(ecodes.EV_REL, ecodes.REL_HWHEEL_HI_RES, -70),
                call.write(ecodes.EV_REL, ecodes.REL_WHEEL_HI_RES, -80),
                call.write(ecodes.EV_REL, ecodes.REL_HWHEEL, clicks),
                call.write(ecodes.EV_REL, ecodes.REL_WHEEL, clicks),
                call.syn(),
            ])
        self.assertEqual(self.scroll.method_calls, expected_frames)
        self.scroll.__exit__.assert_called_once()
        self.pen.write.assert_not_called()

    def test_opening_scroll_failure_closes_pen(self):
        self.factory.side_effect = [self.pen, PermissionError(errno.EACCES, "Permission denied")]

        with self.assertRaises(PermissionError) as failure:
            with UInputDevice(24000, 13500):
                self.fail("A roda virtual deveria ter falhado ao abrir.")

        self.assertEqual(failure.exception.filename, "/dev/uinput")
        self.pen.__exit__.assert_called_once()
