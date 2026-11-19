
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from threading import Thread
from typing import Callable, Iterator

from .browser import open_browser
from .client import watch_disconnect
from .tunnel import reverse_tunnel


@dataclass(frozen=True)
class AdbConnection:
    serial: str
    transport_id: str

    def open_page(self, url: str) -> None:
        Thread(target=open_browser, args=(self.transport_id, url), daemon=True).start()

    def tunnel(self, port: int) -> AbstractContextManager[None]:
        return reverse_tunnel(self.transport_id, port)

    @contextmanager
    def watch_disconnect(self) -> Iterator[Callable[[], bool]]:
        with watch_disconnect(self.transport_id) as process:
            def disconnected() -> bool:
                return process.poll() is not None

            yield disconnected
