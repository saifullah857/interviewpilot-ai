"""Rejects NUL characters before they reach the database. PostgreSQL refuses them in text (SQLite does not), so without this a hostile
`\\u0000` in a path, query string or JSON field would be a server error on one database and silently stored on the other."""

import json

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.errors import AppError

MAX_JSON_BYTES = 1_048_576
BODY_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def has_nul(obj) -> bool:
    stack = [obj]
    while stack:
        cur = stack.pop()
        if isinstance(cur, str):
            if "\x00" in cur:
                return True
        elif isinstance(cur, dict):
            stack.extend(cur.keys())
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
    return False


def _reject(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(AppError(status, code, message).body(), status_code=status)


class RejectNul:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http" or not scope["path"].startswith("/api/"):
            return await self.app(scope, receive, send)
        target = scope.get("raw_path", b"") + b"?" + scope.get("query_string", b"")
        if b"\x00" in target or b"%00" in target.lower():
            return await _reject(400, "invalid_input", "The request contains characters that are not allowed.")(scope, receive, send)
        ctype = dict(scope["headers"]).get(b"content-type", b"")
        if scope["method"] in BODY_METHODS and b"application/json" in ctype:
            body, more = b"", True
            while more:
                msg = await receive()
                if msg["type"] == "http.disconnect":
                    return None
                body += msg.get("body", b"")
                more = msg.get("more_body", False)
                if len(body) > MAX_JSON_BYTES:
                    return await _reject(413, "too_large", "The request is too large.")(scope, receive, send)
            try:
                bad = has_nul(json.loads(body)) if body else False
            except ValueError:
                bad = b"\x00" in body  # not valid JSON: the normal validation error follows, unless it hides a raw NUL
            if bad:
                return await _reject(422, "invalid_input", "Text can't contain null characters.")(scope, receive, send)
            sent = False

            async def replay():
                nonlocal sent
                if not sent:
                    sent = True
                    return {"type": "http.request", "body": body, "more_body": False}
                return await receive()

            return await self.app(scope, replay, send)
        return await self.app(scope, receive, send)
