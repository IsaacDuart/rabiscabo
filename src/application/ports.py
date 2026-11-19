
from contextlib import AbstractContextManager
from typing import Callable, Protocol

from src.domain.models.area import DrawingArea
from src.domain.session import DrawingSession


class USBTunnelError(RuntimeError):
    pass


class AndroidConnection(Protocol):
    @property
    def serial(self) -> str: ...

    def open_page(self, url: str) -> None: ...

    def tunnel(self, port: int) -> AbstractContextManager[None]: ...

    def watch_disconnect(self) -> AbstractContextManager[Callable[[], bool]]: ...


class AndroidDevices(Protocol):
    def select(self) -> AndroidConnection: ...

    def find(self, serial: str) -> AndroidConnection | None: ...


class PageEndpoint(Protocol):
    @property
    def port(self) -> int: ...

    @property
    def url(self) -> str: ...


ServePage = Callable[[DrawingSession, DrawingArea], AbstractContextManager[PageEndpoint]]
Notify = Callable[[str], None]
