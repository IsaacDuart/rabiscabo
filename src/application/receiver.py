
from threading import Event

from src.config.settings import INTERVALO_RECONEXAO
from src.domain.models.area import DrawingArea
from src.domain.session import DrawingTarget

from .link import serve_link
from .ports import AndroidConnection, AndroidDevices, Notify, ServePage, USBTunnelError

RETRY_SECONDS = INTERVALO_RECONEXAO
WAITING_MESSAGE = "Aguardando o mesmo Android voltar pelo cabo USB…"


class Receiver:
    def __init__(self, devices: AndroidDevices, serve_page: ServePage, notify: Notify):
        self._devices = devices
        self._serve_page = serve_page
        self._notify = notify

    def run(self, target: DrawingTarget, area: DrawingArea, stopped: Event) -> None:
        connection: AndroidConnection | None = self._devices.select()
        serial = connection.serial
        previous_error: str | None = None
        self._notify("Mesa USB pronta. Ctrl+C encerra.")

        while connection is not None and not stopped.is_set():
            try:
                serve_link(target, area, connection, stopped, self._serve_page, self._notify)
                previous_error = None
            except USBTunnelError as error:
                message = str(error)
                if message != previous_error:
                    self._notify(message)
                    self._notify(WAITING_MESSAGE)
                previous_error = message

            if stopped.is_set():
                break
            if previous_error is None:
                self._notify(WAITING_MESSAGE)
            connection = self._wait_for_reconnect(serial, stopped)

    def _wait_for_reconnect(self, serial: str, stopped: Event) -> AndroidConnection | None:
        while not stopped.wait(RETRY_SECONDS):
            try:
                connection = self._devices.find(serial)
            except RuntimeError:
                continue  
            if connection is not None:
                return connection
        return None
