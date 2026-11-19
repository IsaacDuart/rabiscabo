import errno
from contextlib import ExitStack
from http.client import HTTPConnection
import json
import unittest
from unittest.mock import Mock

from src.domain.models.area import DrawingArea
from src.domain.enums.tool_state import ToolState
from src.domain.models import PenEvent
from src.domain.session import DrawingSession
from src.adapters.input.http.server import serve_local

CLIENT = "9e36bccf-f44c-4ece-80f3-9eb79e7cf22e"
DOWN_FRAME = [2, 32768, 65535, 4095]


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.tablet = Mock()
        resources = ExitStack()
        self.addCleanup(resources.close)
        try:
            self.server = resources.enter_context(
                serve_local(DrawingSession(self.tablet), DrawingArea(240, 135)),
            )
        except OSError as error:
            if error.errno in {errno.EPERM, errno.EACCES}:
                self.skipTest("Socket de loopback bloqueado pelo ambiente")
            raise
        self.connection = HTTPConnection(self.server.host, timeout=3)
        self.addCleanup(self.connection.close)

    def send(self, seq=1, frames=(), **overrides):
        headers = {
            "Authorization": "Bearer " + self.server.token,
            "Origin": self.server.origin,
            "Content-Type": "application/json",
        }
        headers.update(overrides)
        self.connection.request("POST", "/events", json.dumps([CLIENT, seq, frames]), headers)
        response = self.connection.getresponse()
        response.read()
        return response.status

    def test_draws_after_authorization_and_checks_replay(self):
        self.assertEqual(self.send(), 204)
        self.assertEqual(self.send(2, [DOWN_FRAME]), 204)
        self.assertEqual(self.send(2, [DOWN_FRAME]), 409)
        self.tablet.send.assert_called_once_with(PenEvent(ToolState.DOWN, 32768, 65535, 4095))

    def test_blocks_wrong_token_origin_host_and_malformed_frame(self):
        self.assertEqual(self.send(Authorization="Bearer invalid"), 403)
        self.assertEqual(self.send(Origin="http://another.local"), 403)
        self.assertEqual(self.send(Host="another.local"), 403)
        self.assertEqual(self.send(1, [[2, 0, 0, 0]]), 400)
        self.tablet.send.assert_not_called()

    def test_rejects_oversized_body_and_wrong_content_type(self):
        self.assertEqual(self.send(frames=["x" * 2048]), 400)
        self.assertEqual(self.send(**{"Content-Type": "text/plain"}), 400)
        self.assertEqual(self.send(), 204)

    def test_ui_is_served_locally(self):
        self.connection.request("GET", "/")
        response = self.connection.getresponse()
        self.assertEqual(response.status, 200)
        self.assertIn("frame-ancestors 'none'", response.getheader("Content-Security-Policy"))
        self.assertIn(b"Mesa USB", response.read())
        self.connection.request("GET", "/area.json")
        response = self.connection.getresponse()
        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(response.read()), [240, 135])
        self.connection.request("GET", "/", headers={"Sec-Fetch-Site": "cross-site"})
        response = self.connection.getresponse()
        self.assertEqual(response.status, 403)
        response.read()

    def test_browser_receives_protocol_limits(self):
        self.connection.request("GET", "/protocol.js")
        response = self.connection.getresponse()
        self.assertEqual(response.status, 200)
        script = response.read().decode()
        payload = script.removeprefix("export const protocol = ").removesuffix(";")
        protocol = json.loads(payload)
        from src.config.settings import MAX_COORDINATE, MAX_EVENTS, MAX_PRESSURE, MAX_SCROLL
        self.assertEqual(protocol["maxCoordinate"], MAX_COORDINATE)
        self.assertEqual(protocol["maxPressure"], MAX_PRESSURE)
        self.assertEqual(protocol["maxEvents"], MAX_EVENTS)
        self.assertEqual(protocol["maxScroll"], MAX_SCROLL)

    def test_only_serves_application_routes(self):
        for path in ("/docs", "/openapi.json", "/pad.js?extra=1"):
            with self.subTest(path=path):
                self.connection.request("GET", path)
                response = self.connection.getresponse()
                self.assertEqual(response.status, 404)
                response.read()

    def test_allows_android_intent_navigation_without_allowing_external_embeds(self):
        headers = {"Sec-Fetch-Site": "cross-site", "Sec-Fetch-Mode": "navigate"}
        for destination, expected in [("document", 200), ("iframe", 403)]:
            with self.subTest(destination=destination):
                self.connection.request("GET", "/", headers={
                    **headers, "Sec-Fetch-Dest": destination,
                })
                response = self.connection.getresponse()
                self.assertEqual(response.status, expected)
                response.read()
