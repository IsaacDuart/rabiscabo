
import secrets
import socket
from contextlib import contextmanager
from dataclasses import dataclass
from threading import Thread
from time import monotonic, sleep
from typing import Iterator

import uvicorn

from src.config.settings import (
    LIMITE_CONEXOES_HTTP,
    LOOPBACK,
    TEMPO_ENCERRAMENTO_HTTP,
    TEMPO_KEEP_ALIVE_HTTP,
)
from src.domain.models.area import DrawingArea
from src.domain.session import DrawingSession
from .app import create_app

@dataclass(frozen=True)
class LocalEndpoint:
    port: int
    token: str

    @property
    def host(self) -> str:
        return f"{LOOPBACK}:{self.port}"

    @property
    def origin(self) -> str:
        return f"http://{self.host}"

    @property
    def url(self) -> str:
        return f"{self.origin}/#{self.token}"


@contextmanager
def serve_local(session: DrawingSession, area: DrawingArea) -> Iterator[LocalEndpoint]:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind((LOOPBACK, 0))
        endpoint = LocalEndpoint(listener.getsockname()[1], secrets.token_urlsafe(32))
        app = create_app(session, area, host=endpoint.host, token=endpoint.token)
        config = uvicorn.Config(
            app,
            http="h11",
            ws="none",
            lifespan="off",
            proxy_headers=False,
            access_log=False,
            server_header=False,
            date_header=False,
            limit_concurrency=LIMITE_CONEXOES_HTTP,
            timeout_keep_alive=TEMPO_KEEP_ALIVE_HTTP,
            timeout_graceful_shutdown=TEMPO_ENCERRAMENTO_HTTP,
            log_level="warning",
        )
        server = uvicorn.Server(config)
        thread = Thread(target=server.run, kwargs={"sockets": [listener]}, name="mesa-http")
        thread.start()
        try:
            deadline = monotonic() + 3
            while not server.started:
                if not thread.is_alive() or monotonic() >= deadline:
                    raise RuntimeError("Falha ao iniciar o servidor HTTP local.")
                sleep(0.01)
            yield endpoint
        finally:
            server.should_exit = True
            thread.join()
