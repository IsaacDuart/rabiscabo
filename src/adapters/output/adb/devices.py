
from .client import run_adb
from .connection import AdbConnection


class AdbDevices:
    def select(self) -> AdbConnection:
        try:
            serial = run_adb("-d", "get-serialno")
        except RuntimeError as error:
            raise RuntimeError(
                f"{error}\nConecte um único Android por cabo e autorize a depuração USB."
            ) from None
        connection = self.find(serial)
        if connection is None:
            raise RuntimeError("O Android precisa estar conectado por USB e autorizado no ADB.")
        return connection

    def find(self, serial: str) -> AdbConnection | None:
        for line in run_adb("devices", "-l").splitlines():
            connection = _parse_usb(line, serial)
            if connection is not None:
                return connection
        return None


def _parse_usb(line: str, serial: str) -> AdbConnection | None:
    fields = line.split()
    if fields[:2] != [serial, "device"]:
        return None

    properties = dict(field.split(":", 1) for field in fields[2:] if ":" in field)
    transport_id = properties.get("transport_id", "")
    if "usb" in properties and transport_id.isdecimal():
        return AdbConnection(serial, transport_id)
    return None
