
from threading import Event
from time import monotonic

from src.config.settings import INTERVALO_VERIFICACAO, TEMPO_ABERTURA_PAGINA
from src.domain.models.area import DrawingArea
from src.domain.session import DrawingSession, DrawingTarget

from .ports import AndroidConnection, Notify, ServePage

PAGE_TIMEOUT_SECONDS = TEMPO_ABERTURA_PAGINA
CHECK_INTERVAL_SECONDS = INTERVALO_VERIFICACAO


def serve_link(
    target: DrawingTarget,
    area: DrawingArea,
    connection: AndroidConnection,
    stopped: Event,
    serve_page: ServePage,
    notify: Notify,
) -> None:
    session = DrawingSession(target)
    with serve_page(session, area) as page, connection.tunnel(page.port):
        with connection.watch_disconnect() as disconnected:
            try:
                connection.open_page(page.url)
                launch_deadline = monotonic() + PAGE_TIMEOUT_SECONDS
                connection_announced = False
                while not stopped.is_set() and not disconnected():
                    session.expire()
                    if session.connected and not connection_announced:
                        notify("Android conectado por USB.")
                        connection_announced = True
                        launch_deadline = None
                    elif launch_deadline is not None and monotonic() >= launch_deadline:
                        notify(f"Abra este endereço no Chrome do Android:\n{page.url}")
                        launch_deadline = None
                    stopped.wait(CHECK_INTERVAL_SECONDS)
            finally:
                session.close()
