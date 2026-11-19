import json
import unittest

from src.domain.enums.tool_state import ToolState
from src.domain.models import DrawingBatch, PenEvent, ScrollEvent
from src.adapters.input.http.codec import decode_batch

CLIENT = "9e36bccf-f44c-4ece-80f3-9eb79e7cf22e"
DOWN_FRAME = [2, 32768, 65535, 4095]


class CodecTests(unittest.TestCase):
    def test_decodes_complete_batch(self):
        body = json.dumps([CLIENT, 2, [DOWN_FRAME, [0, 32768, 65535, 0]]]).encode()
        expected_events = (
            PenEvent(ToolState.DOWN, 32768, 65535, 4095),
            PenEvent(ToolState.OUT, 32768, 65535, 0),
        )
        self.assertEqual(decode_batch(body), DrawingBatch(CLIENT, 2, expected_events))

    def test_rejects_invalid_sample_and_sequence(self):
        for sequence, frame in [
            (True, DOWN_FRAME), (0, DOWN_FRAME), (2**53, DOWN_FRAME),
            (1, [True, 1, 1, 0]), (1, [2, 65536, 0, 1]),
            (1, [1, 0, 0, 1]), (1, [2, 0, 0, 0]), (1, [5, 0, 0, 0]),
            (1, [2, 0, 0, 0.5]),
            (1, [3, 961, 0, 0]), (1, [3, 0, -961, 0]), (1, [3, 0, 0, 0]),
            (1, [3, 100, -200, 1]),
        ]:
            with self.subTest(sequence=sequence, frame=frame), self.assertRaises(ValueError):
                decode_batch(json.dumps([CLIENT, sequence, [frame]]).encode())

    def test_decodes_signed_scroll_axes(self):
        body = json.dumps([CLIENT, 2, [[3, 70, -80, 0]]]).encode()
        self.assertEqual(decode_batch(body).events, (ScrollEvent(70, -80),))
