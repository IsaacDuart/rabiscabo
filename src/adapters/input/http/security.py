
import secrets

from fastapi import Request, Response
from starlette.middleware.base import RequestResponseEndpoint

SECURITY_HEADERS = {
    "Cache-Control": "no-store",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Resource-Policy": "same-origin",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": (
        "default-src 'none'; script-src 'self'; style-src 'self'; "
        "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
    ),
}


class LocalAccess:
    def __init__(self, host: str, token: str):
        self._host = host
        self._origin = f"http://{host}"
        self._authorization = f"Bearer {token}".encode("ascii")

    async def protect(
        self, request: Request, call_next: RequestResponseEndpoint,
    ) -> Response:
        if request.headers.getlist("host") == [self._host]:
            response = await call_next(request)
        else:
            response = Response(status_code=403)
        response.headers.update(SECURITY_HEADERS)
        if response.status_code >= 400:
            response.headers["Connection"] = "close"
        return response

    def permits_events(self, request: Request) -> bool:
        credentials = request.headers.getlist("authorization")
        return (
            request.headers.getlist("origin") == [self._origin]
            and len(credentials) == 1
            and secrets.compare_digest(credentials[0].encode("latin-1"), self._authorization)
        )


def permits_page(request: Request) -> bool:
    if request.headers.get("sec-fetch-site") not in {"cross-site", "same-site"}:
        return True
    
    return (
        request.scope["raw_path"] == b"/"
        and not request.scope["query_string"]
        and request.headers.get("sec-fetch-mode") == "navigate"
        and request.headers.get("sec-fetch-dest") == "document"
    )
