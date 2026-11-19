
from fastapi import FastAPI

from src.domain.models.area import DrawingArea
from src.domain.session import DrawingSession
from .routes.events import event_routes
from .routes.pages import page_routes
from .security import LocalAccess


def create_app(session: DrawingSession, area: DrawingArea, *, host: str, token: str) -> FastAPI:
    app = FastAPI(openapi_url=None, redirect_slashes=False)
    access = LocalAccess(host, token)
    app.middleware("http")(access.protect)
    app.include_router(event_routes(session, access))
    app.include_router(page_routes(area))
    return app
