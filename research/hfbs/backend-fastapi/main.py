"""
main.py — FastAPI Application Entry Point
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Запуск: uvicorn main:app --host 0.0.0.0 --port 8001 --reload

Ключевые особенности по сравнению с Django:
  1. Lifespan — управление ресурсами при старте/остановке
  2. Все роутеры используют async def
  3. Dependency Injection встроен в FastAPI (Depends)
  4. Автодокументация: http://localhost:8001/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from core.redis import init_redis, close_redis
from services.event_service import init_kafka_producer, stop_kafka_producer
from routers import events, seats, orders, payments, tickets, auth


# ── Lifespan: startup / shutdown ──────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Выполняется при старте и остановке приложения.
    Инициализируем Redis и Kafka producer.
    """
    print("🚀 FastAPI HFBS starting...")
    await init_redis()
    await init_kafka_producer()
    print("✅ Redis & Kafka initialized")

    yield  # Приложение работает

    print("🛑 FastAPI HFBS stopping...")
    await close_redis()
    await stop_kafka_producer()


# ── Application ───────────────────────────────────────────────
app = FastAPI(
    title="HFBS FastAPI (Async)",
    description="""
    ## High-Frequency Booking System — Async Backend

    **Ключевые особенности:**
    - Async/await на всех уровнях (DB, Redis, Kafka)
    - Event-driven архитектура
    - Redis-блокировки для race condition защиты
    - JWT аутентификация
    - PDF генерация билетов

    [Django (sync) version](http://localhost:8000/api/docs/)
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static Files (PDF tickets) ────────────────────────────────
media_dir = os.path.join(os.path.dirname(__file__), "media")
os.makedirs(media_dir, exist_ok=True)
app.mount("/media", StaticFiles(directory=media_dir), name="media")

# ── Routers ───────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(events.router)
app.include_router(seats.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(tickets.router)


@app.get("/health", tags=["Health"])
async def health_check():
    """Проверка работоспособности сервиса."""
    return {"status": "ok", "backend": "fastapi-async", "version": "1.0.0"}
