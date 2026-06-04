import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from common.custom_logger import set_correlation_id

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Читаем Correlation ID из заголовка или генерируем новый
        correlation_id = request.headers.get("X-Request-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Устанавливаем в контекст для текущего запроса
        set_correlation_id(correlation_id)

        # Добавляем в ответ для отладки
        response = await call_next(request)
        response.headers["X-Request-ID"] = correlation_id
        return response
