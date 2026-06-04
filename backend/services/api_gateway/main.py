import httpx
import jwt
import logging
from typing import Any, Final

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from common.exception_handlers import setup_exception_handlers
from common.custom_logger import setup_logging, get_correlation_id
from common.middleware import CorrelationIdMiddleware
from services.api_gateway.config import ADMIN_PREFIXES, PROTECTED_PREFIXES, ROUTES, settings

setup_logging("api_gateway")
logger = logging.getLogger(__name__)

STRIPPED_RESPONSE_HEADERS: Final[frozenset[str]] = frozenset({
    "x-user-id",
    "x-user-role",
    "server",
    "x-powered-by",
    # hop-by-hop (RFC 2616 §13.5.1)
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
})

app = FastAPI(
    title="API Gateway",
    version="1.0.0",
)
app.add_middleware(CorrelationIdMiddleware)
setup_exception_handlers(app)


def custom_openapi() -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    # Один catch-all маршрут — помечаем операции как использующие Bearer (опционально для клиента).
    for path_key, path_item in openapi_schema.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.lower() not in ("get", "post", "put", "delete", "patch", "head"):
                continue
            if not isinstance(operation, dict):
                continue
            operation.setdefault("security", [{"BearerAuth": []}])
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Temporary permissive CORS for frontend integration.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = httpx.AsyncClient(timeout=60.0)


@app.on_event("shutdown")
async def shutdown_event():
    await client.aclose()


def verify_token(request: Request) -> dict:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def _safe_response_headers(raw_headers: httpx.Headers) -> dict[str, str]:
    return {
        k: v
        for k, v in raw_headers.items()
        if k.lower() not in STRIPPED_RESPONSE_HEADERS
    }


def _drop_header_case_insensitive(headers: dict[str, str], header_name: str) -> None:
    target = header_name.lower()
    for key in list(headers.keys()):
        if key.lower() == target:
            headers.pop(key, None)


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def gateway_proxy(path: str, request: Request):
    full_path = f"/{path}"

    target_service_url = None
    for prefix, url in ROUTES.items():
        if full_path.startswith(prefix):
            target_service_url = url
            break

    if not target_service_url:
        raise HTTPException(status_code=404, detail="Route not found in API Gateway")

    user_id = None
    role = None

    is_protected = any(full_path.startswith(p) for p in PROTECTED_PREFIXES)
    is_admin = any(full_path.startswith(p) for p in ADMIN_PREFIXES)

    if is_protected or is_admin:
        payload = verify_token(request)
        user_id = payload.get("sub")
        role = payload.get("role")

        if is_admin and role != "admin":
            raise HTTPException(status_code=403, detail="Admin privileges required")

    target_url = f"{target_service_url}{full_path}"

    body = await request.body()
    headers = dict(request.headers)

    _drop_header_case_insensitive(headers, "host")
    _drop_header_case_insensitive(headers, "content-length")
    # Never trust caller-provided identity headers.
    _drop_header_case_insensitive(headers, "x-user-id")
    _drop_header_case_insensitive(headers, "x-user-role")

    if user_id:
        headers["X-User-Id"] = str(user_id)
        headers["X-User-Role"] = str(role)

    headers["X-Request-ID"] = get_correlation_id()

    try:
        logger.info(f"Proxying {request.method} {full_path} -> {target_url}")
        response = await client.request(
            method=request.method, url=target_url, headers=headers, params=request.query_params, content=body
        )
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

    safe_headers = _safe_response_headers(response.headers)
    safe_headers["X-Request-ID"] = get_correlation_id()

    return Response(content=response.content, status_code=response.status_code, headers=safe_headers)
