import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from common.custom_logger import get_correlation_id
from common.errors import BusinessLogicError, NotFoundError

logger = logging.getLogger(__name__)


def _json(status_code: int, body: dict[str, Any]) -> JSONResponse:
    headers: dict[str, str] = {}
    corr_id = get_correlation_id()
    if corr_id:
        headers["X-Request-ID"] = corr_id
    return JSONResponse(status_code=status_code, content=body, headers=headers)


async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
    return _json(404, {"detail": str(exc)})


async def business_logic_handler(_request: Request, exc: BusinessLogicError) -> JSONResponse:
    return _json(400, {"detail": str(exc)})


async def validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for err in exc.errors():
        errors.append({
            "loc": list(err.get("loc", [])),
            "msg": err.get("msg", ""),
            "type": err.get("type", ""),
        })
    return _json(422, {"detail": "Validation error", "errors": errors})


async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _json(exc.status_code, {"detail": exc.detail})


async def integrity_error_handler(_request: Request, exc: IntegrityError) -> JSONResponse:
    db_error_text = str(getattr(exc, "orig", exc)).lower()
    corr_id = get_correlation_id() or "N/A"

    if "duplicate key value violates unique constraint" in db_error_text:
        logger.warning("IntegrityError(unique) [ReqID: %s]: %s", corr_id, exc)
        return _json(409, {"detail": "Resource with these fields already exists"})

    if "violates foreign key constraint" in db_error_text:
        logger.warning("IntegrityError(fk) [ReqID: %s]: %s", corr_id, exc)
        return _json(409, {"detail": "Referenced entity does not exist"})

    if "null value in column" in db_error_text and "violates not-null constraint" in db_error_text:
        logger.warning("IntegrityError(not-null) [ReqID: %s]: %s", corr_id, exc)
        return _json(400, {"detail": "Required field is missing"})

    logger.warning("IntegrityError(other) [ReqID: %s]: %s", corr_id, exc, exc_info=True)
    return _json(400, {"detail": "Data integrity error"})


async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    corr_id = get_correlation_id() or "N/A"
    logger.error("Unhandled exception [ReqID: %s]: %s", corr_id, exc, exc_info=True)
    return _json(500, {"detail": "Internal server error"})


def setup_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(NotFoundError, not_found_handler)
    app.add_exception_handler(BusinessLogicError, business_logic_handler)
    app.add_exception_handler(RequestValidationError, validation_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
