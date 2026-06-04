"""
routers/seats.py — Seat API Router (FastAPI)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Идентичные эндпоинты с Django, но async.

GET  /api/v1/seats/?event_id=<id>  — список мест
POST /api/v1/seats/<id>/reserve/   — блокировка места
POST /api/v1/seats/<id>/release/   — отмена брони
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from core.database import get_db
from core.redis import get_redis
from core.security import get_current_user
from services.seat_service import AsyncSeatService, SeatLockError
from schemas.schemas import SeatOut, ReserveSeatResponse

router = APIRouter(prefix="/api/v1/seats", tags=["Seats"])


@router.get("/", response_model=list[SeatOut], summary="Список мест события")
async def seat_list(
    event_id: int = Query(..., description="ID события"),
    db: AsyncSession = Depends(get_db),
):
    """
    Возвращает все места для события.
    Открытый эндпоинт — авторизация не нужна.
    """
    seats = await AsyncSeatService.get_seats_for_event(event_id=event_id, db=db)
    return seats


@router.post(
    "/{seat_id}/reserve/",
    response_model=ReserveSeatResponse,
    status_code=status.HTTP_200_OK,
    summary="Забронировать место (async Redis lock)",
    responses={409: {"description": "Место уже занято"}},
)
async def reserve_seat(
    seat_id: int,
    db: AsyncSession      = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    user: dict            = Depends(get_current_user),
):
    """
    Атомарно блокирует место через Redis SET NX.
    HTTP 409 — если место занято (race condition защита).

    FastAPI обрабатывает тысячи таких запросов одновременно
    без создания новых потоков — благодаря async/await.
    """
    try:
        seat = await AsyncSeatService.reserve_seat(
            seat_id=seat_id,
            user_id=user["user_id"],
            db=db,
            redis=redis,
        )
        return ReserveSeatResponse(
            message="Место успешно забронировано",
            seat=SeatOut.model_validate(seat),
            lock_ttl_seconds=300,
        )
    except SeatLockError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Внутренняя ошибка")


@router.post("/{seat_id}/release/", summary="Отменить бронь")
async def release_seat(
    seat_id: int,
    db: AsyncSession      = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    user: dict            = Depends(get_current_user),
):
    await AsyncSeatService.release_seat(seat_id=seat_id, db=db, redis=redis)
    return {"message": "Бронь отменена"}
