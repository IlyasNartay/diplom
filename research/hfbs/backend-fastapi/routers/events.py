"""
routers/events.py — Events Router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from models.db_models import Event
from schemas.schemas import EventOut

router = APIRouter(prefix="/api/v1/events", tags=["Events"])


@router.get("/", response_model=list[EventOut], summary="Список событий")
async def event_list(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Event).where(Event.is_active == True).order_by(Event.date))
    return result.scalars().all()


@router.get("/{event_id}/", response_model=EventOut, summary="Детали события")
async def event_detail(event_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Event).where(Event.id == event_id, Event.is_active == True))
    event  = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    return event
