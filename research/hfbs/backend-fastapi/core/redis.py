"""
core/redis.py — Async Redis Client
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
КЛЮЧЕВОЕ ОТЛИЧИЕ от Django:
  - redis.asyncio вместо django-redis (sync)
  - SET NX EX — атомарная операция в Redis (как SETNX + EXPIRE)
  - await не блокирует — другие корутины продолжают работу

В Django:
  cache.add(key, val, timeout) — синхронно, блокирует поток

В FastAPI:
  await redis.set(key, val, nx=True, ex=ttl) — асинхронно
"""
import redis.asyncio as aioredis
from core.config import settings

# Глобальный Redis-клиент (создаётся при старте приложения)
redis_client: aioredis.Redis | None = None


async def init_redis() -> None:
    """Инициализация Redis при старте FastAPI приложения."""
    global redis_client
    redis_client = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        max_connections=50,
    )


async def close_redis() -> None:
    """Закрытие соединения при остановке."""
    if redis_client:
        await redis_client.aclose()


def get_redis() -> aioredis.Redis:
    """Dependency для FastAPI: redis: Redis = Depends(get_redis)"""
    return redis_client
