
import json
from pathlib import Path

from fastapi import APIRouter, Request, Response

from src.domain.models.area import DrawingArea
from .security import permits_page

WEB = Path(__file__).with_name("web")
ASSETS = {
    b"/": ("index.html", "text/html; charset=utf-8"),
    b"/style.css": ("style.css", "text/css; charset=utf-8"),
    b"/pad.js": ("pad.js", "text/javascript; charset=utf-8"),
    b"/ink.js": ("ink.js", "text/javascript; charset=utf-8"),
    b"/transport.js": ("transport.js", "text/javascript; charset=utf-8"),
    b"/touch.js": ("touch.js", "text/javascript; charset=utf-8"),
}


def page_routes(area: DrawingArea) -> APIRouter:
    router = APIRouter()
    assets = {
        path: (mime, (WEB / filename).read_bytes())
        for path, (filename, mime) in ASSETS.items()
    }
    dimensions = json.dumps([area.width, area.height]).encode()
    assets[b"/area.json"] = ("application/json", dimensions)

    @router.get("/{path:path}")
    async def get_asset(request: Request) -> Response:
        if not permits_page(request):
            return Response(status_code=403)
        asset = assets.get(request.scope["raw_path"])
        if asset is None or request.scope["query_string"]:
            return Response(status_code=404)
        mime, content = asset
        return Response(content, media_type=mime)

    return router
