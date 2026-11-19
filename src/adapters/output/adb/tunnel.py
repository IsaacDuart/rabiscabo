
from contextlib import contextmanager
from typing import Iterator

from src.application.ports import USBTunnelError

from .wire import reverse_command


@contextmanager
def reverse_tunnel(transport_id: str, port: int) -> Iterator[None]:
    remote = f"tcp:localhost:{port}"
    try:
        resolved = reverse_command(transport_id, f"forward:norebind:{remote};tcp:{port}")
    except (OSError, RuntimeError) as error:
        raise USBTunnelError(f"Falha ao abrir o túnel USB. {error}") from error

    
    listener = f"tcp:{port}" if resolved == str(port).encode("ascii") else remote
    try:
        yield
    finally:
        try:
            reverse_command(transport_id, f"killforward:{listener}")
        except (OSError, RuntimeError):
            pass  
