
import socket

from src.config.settings import LOOPBACK


def _send(wire, command):
    payload = command.encode("ascii")
    wire.write(f"{len(payload):04x}".encode("ascii") + payload)


def _status(wire):
    status = wire.read(4)
    if status == b"OKAY":
        return
    if status == b"FAIL":
        try:
            size = int(wire.read(4), 16)
        except ValueError:
            raise RuntimeError("Resposta inválida do servidor ADB.") from None
        detail = wire.read(size).decode("utf-8", "replace")
        raise RuntimeError(f"ADB: {detail}")
    raise RuntimeError("O servidor ADB encerrou o comando sem confirmar.")


def reverse_command(transport_id: str, command: str) -> bytes:
    
    
    with socket.create_connection((LOOPBACK, 5037), timeout=3) as connection:
        with connection.makefile("rwb") as wire:
            _send(wire, f"host:transport-id:{transport_id}")
            wire.flush()
            _status(wire)
            _send(wire, f"reverse:{command}")
            wire.flush()
            _status(wire)  
            _status(wire)  
            
            prefix = wire.read(4)
            if not prefix:
                return b""
            try:
                size = int(prefix, 16)
            except ValueError:
                raise RuntimeError("Resposta inválida do servidor ADB.") from None
            return wire.read(size)
