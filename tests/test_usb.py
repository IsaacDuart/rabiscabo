from contextlib import nullcontext
from io import BytesIO
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

from src.adapters.output.adb.browser import open_browser
from src.adapters.output.adb.connection import AdbConnection
from src.adapters.output.adb.devices import AdbDevices
from src.adapters.output.adb.tunnel import reverse_tunnel
from src.adapters.output.adb.wire import reverse_command
from src.domain.models.area import DrawingArea
from src.application.receiver import Receiver


class ADBTests(unittest.TestCase):
    @patch("src.adapters.output.adb.browser.run_adb")
    def test_prefers_chrome_and_falls_back_to_default_browser(self, adb):
        adb.side_effect = [RuntimeError("Chrome ausente"), "Status: ok"]
        self.assertTrue(open_browser("5", "http://127.0.0.1:33817/#test"))
        first, second = [request.args for request in adb.call_args_list]
        self.assertEqual(first, (*second, "-p", "com.android.chrome"))

    @patch("src.adapters.output.adb.devices.run_adb")
    def test_resolves_only_usb_transport(self, adb):
        adb.side_effect = [
            "MY_ANDROID",
            "List of devices attached\n"
            "MY_ANDROID device product:mock transport_id:4\n"
            "MY_ANDROID device usb:1-1 model:phone transport_id:5\n",
        ]
        self.assertEqual(AdbDevices().select(), AdbConnection("MY_ANDROID", "5"))

    @patch("src.adapters.output.adb.devices.run_adb")
    def test_reconnects_same_authorized_usb_device_with_new_transport(self, adb):
        adb.side_effect = [
            "MY_ANDROID",
            "MY_ANDROID device usb:1-1 transport_id:5",
            "OTHER_ANDROID device usb:1-1 transport_id:6",
            "MY_ANDROID unauthorized usb:1-1 transport_id:7",
            "MY_ANDROID device transport_id:8",
            "MY_ANDROID device usb:1-2 transport_id:9",
        ]
        tablet = Mock()
        area = DrawingArea(240, 135)
        stopped = Event()

        pages = [
            SimpleNamespace(port=33817, url="http://127.0.0.1:33817/#first"),
            SimpleNamespace(port=33818, url="http://127.0.0.1:33818/#second"),
        ]
        serve_page = Mock(side_effect=[nullcontext(page) for page in pages])
        receiver = Receiver(AdbDevices(), serve_page, Mock())

        def monitor_disconnect(transport_id):
            def poll():
                if transport_id == "9":
                    stopped.set()
                return 0
            return nullcontext(SimpleNamespace(poll=poll))

        with (
            patch("src.application.receiver.RETRY_SECONDS", 0),
            patch("src.adapters.output.adb.connection.reverse_tunnel", side_effect=lambda *_: nullcontext())
            as tunnel,
            patch("src.adapters.output.adb.connection.watch_disconnect", side_effect=monitor_disconnect)
            as watch,
            patch.object(AdbConnection, "open_page", autospec=True) as open_page,
        ):
            receiver.run(tablet, area, stopped)

        self.assertEqual(tunnel.call_args_list, [call("5", 33817), call("9", 33818)])
        self.assertEqual(watch.call_args_list, [call("5"), call("9")])
        self.assertEqual(open_page.call_args_list, [
            call(AdbConnection("MY_ANDROID", "5"), pages[0].url),
            call(AdbConnection("MY_ANDROID", "9"), pages[1].url),
        ])
        self.assertEqual(tablet.release.call_count, 2)

    @patch("src.adapters.output.adb.tunnel.reverse_command")
    def test_removes_only_registered_listener(self, command):
        for response, listener in [(b"33817", "tcp:33817"), (b"", "tcp:localhost:33817")]:
            with self.subTest(response=response):
                command.reset_mock()
                command.return_value = response
                with self.assertRaisesRegex(RuntimeError, "encerrado"):
                    with reverse_tunnel("5", 33817):
                        raise RuntimeError("encerrado")
                self.assertEqual(command.call_args_list, [
                    call("5", "forward:norebind:tcp:localhost:33817;tcp:33817"),
                    call("5", "killforward:" + listener),
                ])

    @patch("src.adapters.output.adb.wire.socket.create_connection")
    def test_wire_requires_device_ack_and_reads_resolved_port(self, connect):
        wire = connect.return_value.__enter__.return_value.makefile.return_value.__enter__.return_value
        wire.read.side_effect = BytesIO(b"OKAYOKAYOKAY000533817").read
        self.assertEqual(reverse_command("5", "forward:norebind:tcp:localhost:33817;tcp:33817"),
                         b"33817")
        self.assertEqual(wire.write.call_args_list, [
            call(b"0013host:transport-id:5"),
            call(b"0036reverse:forward:norebind:tcp:localhost:33817;tcp:33817"),
        ])
        wire.read.side_effect = BytesIO(b"OKAYOKAYFAIL0006ocupou").read
        with self.assertRaisesRegex(RuntimeError, "ocupou"):
            reverse_command("5", "forward:norebind:tcp:localhost:33817;tcp:33817")
