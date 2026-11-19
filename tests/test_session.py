import unittest
from unittest.mock import Mock, patch

from src.domain.enums.tool_state import ToolState
from src.domain.models import DrawingBatch, PenEvent
from src.domain.session import LEASE_SECONDS, DrawingSession


class DrawingSessionTests(unittest.TestCase):
    def test_exclusive_ordered_session_releases_on_timeout(self):
        tablet = Mock()
        session = DrawingSession(tablet)
        down = PenEvent(ToolState.DOWN, 32768, 65535, 4095)

        with patch("src.domain.session.monotonic", return_value=10) as now:
            self.assertFalse(session.submit(DrawingBatch("first", 1, (down,))))
            self.assertTrue(session.submit(DrawingBatch("first", 1, ())))
            self.assertTrue(session.submit(DrawingBatch("first", 2, (down,))))
            self.assertFalse(session.submit(DrawingBatch("first", 2, (down,))))
            self.assertFalse(session.submit(DrawingBatch("second", 1, ())))

            now.return_value += LEASE_SECONDS
            session.expire()

            tablet.release.assert_called_once()
            self.assertTrue(session.submit(DrawingBatch("second", 1, ())))
            self.assertFalse(session.submit(DrawingBatch("first", 3, (down,))))

        tablet.send.assert_called_once_with(down)
        session.close()
        self.assertFalse(session.submit(DrawingBatch("second", 2, (down,))))
