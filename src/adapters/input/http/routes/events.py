
import asyncio
import re

from fastapi import APIRouter, Request, Response
from starlette.requests import ClientDisconnect

from src.config.settings import TEMPO_CORPO_HTTP
from src.domain.session import DrawingSession
from ..codec import MAX_BODY, decode_batch
from ..security import LocalAccess

BODY_TIMEOUT_SECONDS = TEMPO_CORPO_HTTP


def _content_length(request: Request) -> int:
    if request.headers.getlist("content-type") != ["application/json"]:
        raise ValueError
    if "transfer-encoding" in request.headers:
        raise ValueError
    lengths = request.headers.getlist("content-length")
    if len(lengths) != 1 or not re.fullmatch(r"[0-9]{1,4}", lengths[0]):
        raise ValueError
    length = int(lengths[0])
    if not 0 < length <= MAX_BODY:
        raise ValueError
    return length


def event_routes(session: DrawingSession, access: LocalAccess) -> APIRouter:
    router = APIRouter()

    @router.post("/events")
    async def post_events(request: Request) -> Response:
        if not access.permits_events(request):
            return Response(status_code=403)
        if request.scope["raw_path"] != b"/events" or request.scope["query_string"]:
            return Response(status_code=404)

        try:
            length = _content_length(request)
            body = await asyncio.wait_for(request.body(), timeout=BODY_TIMEOUT_SECONDS)
            if len(body) != length:
                return Response(status_code=400)
            batch = decode_batch(body)
        except (ValueError, RecursionError, asyncio.TimeoutError, ClientDisconnect):
            return Response(status_code=400)

        try:
            accepted = session.submit(batch)
        except OSError:
            return Response(status_code=503)
        return Response(status_code=204 if accepted else 409)

    return router
