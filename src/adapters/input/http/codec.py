
import json
import re

from src.domain.enums.tool_state import ToolState
from src.domain.models import DrawingBatch, DrawingEvent, PenEvent, ScrollEvent

from src.config.settings import (
    MAX_BODY, MAX_COORDINATE, MAX_EVENTS, MAX_PRESSURE, MAX_SCROLL, MAX_SEQUENCE,
    SCROLL_CODE,
)


def decode_batch(body: bytes) -> DrawingBatch:
    packet = json.loads(body.decode("utf-8"))
    if not isinstance(packet, list) or len(packet) != 3:
        raise ValueError("Pacote inválido")

    client_id, sequence, frames = packet
    if not isinstance(client_id, str) or not re.fullmatch(r"[0-9a-f-]{36}", client_id):
        raise ValueError("Cliente inválido")
    if type(sequence) is not int or not 1 <= sequence <= MAX_SEQUENCE:
        raise ValueError("Sequência inválida")
    if not isinstance(frames, list) or len(frames) > MAX_EVENTS:
        raise ValueError("Lote inválido")

    return DrawingBatch(client_id, sequence, tuple(_decode_event(frame) for frame in frames))


def _decode_event(frame: object) -> DrawingEvent:
    if not isinstance(frame, list) or len(frame) != 4:
        raise ValueError("Amostra inválida")
    if any(type(value) is not int for value in frame):
        raise ValueError("Valores devem ser inteiros")

    code, x, y, pressure = frame
    if code == SCROLL_CODE:
        if pressure != 0 or max(abs(x), abs(y)) > MAX_SCROLL or (x == 0 and y == 0):
            raise ValueError("Rolagem inválida")
        return ScrollEvent(x, y)

    state = ToolState(code)
    if not (0 <= x <= MAX_COORDINATE and 0 <= y <= MAX_COORDINATE and 0 <= pressure <= MAX_PRESSURE):
        raise ValueError("Valor fora da faixa")
    if (state == ToolState.DOWN) != (pressure > 0):
        raise ValueError("Pressão incompatível com o estado da caneta")
    return PenEvent(state, x, y, pressure)
