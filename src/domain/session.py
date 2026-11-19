
from threading import Event, Lock
from time import monotonic
from typing import Protocol

from src.config.settings import TEMPO_SESSAO

from .models import DrawingBatch, DrawingEvent

LEASE_SECONDS = TEMPO_SESSAO


class DrawingTarget(Protocol):
    def send(self, event: DrawingEvent) -> None: ...

    def release(self) -> None: ...


class DrawingSession:
    def __init__(self, target: DrawingTarget):
        self._target = target
        self._lock = Lock()
        self._connected = Event()
        self._owner: str | None = None
        self._sequence = 0
        self._deadline = 0.0
        self._closed = False
        self._error: OSError | None = None

    @property
    def connected(self) -> bool:
        return self._connected.is_set()

    def expire(self) -> None:
        with self._lock:
            if self._error is not None:
                raise self._error
            self._expire_at(monotonic())

    def submit(self, batch: DrawingBatch) -> bool:
        with self._lock:
            if self._closed or self._error is not None:
                return False
            try:
                now = monotonic()
                self._expire_at(now)
                if self._owner is None and not batch.events:
                    self._owner = batch.client_id
                    self._sequence = 0
                if self._owner != batch.client_id or batch.sequence <= self._sequence:
                    return False
                for event in batch.events:
                    self._target.send(event)
                self._sequence = batch.sequence
                self._deadline = now + LEASE_SECONDS
                self._connected.set()
                return True
            except OSError as error:
                self._error = error
                raise

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self._target.release()

    def _expire_at(self, now: float) -> None:
        if self._owner is not None and now >= self._deadline:
            self._target.release()
            self._owner = None
