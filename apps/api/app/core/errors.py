import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger("interviewpilot")


class AppError(Exception):
    def __init__(self, status: int, code: str, message: str, details=None, headers: dict | None = None):
        self.status, self.code, self.message, self.details, self.headers = status, code, message, details, headers

    def body(self) -> dict:
        err: dict = {"code": self.code, "message": self.message}
        if self.details is not None:
            err["details"] = self.details
        return {"error": err}


def error_response(e: AppError) -> JSONResponse:
    return JSONResponse(e.body(), status_code=e.status, headers=e.headers)


def not_authenticated() -> AppError:
    return AppError(401, "not_authenticated", "You need to log in.")


def not_found(what: str = "Resource") -> AppError:
    return AppError(404, "not_found", f"{what} not found.")


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, e: AppError):
        return error_response(e)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, e: RequestValidationError):
        details = [{"field": ".".join(str(p) for p in err["loc"][1:]), "message": err["msg"]} for err in e.errors()]
        return error_response(AppError(422, "validation_error", "Some fields are invalid.", details))

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, e: StarletteHTTPException):
        code = {404: "not_found", 405: "method_not_allowed"}.get(e.status_code, "http_error")
        return error_response(AppError(e.status_code, code, str(e.detail)))

    @app.exception_handler(DataError)
    async def _data_error(_: Request, e: DataError):
        log.warning("Database rejected a value: %s", type(e.orig).__name__)  # the value itself is never logged
        return error_response(AppError(422, "invalid_input", "Some of the text can't be stored. Remove unusual characters and try again."))

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, e: Exception):
        log.exception("Unhandled error")  # details go to the server log only
        return error_response(AppError(500, "internal_error", "Something went wrong on our side."))
