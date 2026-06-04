import uuid
from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from services.orchestrator.database import get_db
from services.orchestrator.logic import saga_manager as saga_manager
from services.orchestrator.logic.saga_manager import SagaManager

router = APIRouter()


class BuyTicketRequest(BaseModel):
    seat_ids: List[uuid.UUID]


def get_saga_manager(request: Request) -> SagaManager:
    return request.app.state.saga_manager


@router.post("/buy")
async def start_booking(
    body: BuyTicketRequest,
    x_user_id: uuid.UUID = Header(...),
    manager: SagaManager = Depends(get_saga_manager),
    db: AsyncSession = Depends(get_db),
):
    if not body.seat_ids:
        raise HTTPException(status_code=400, detail="seat_ids array cannot be empty")

    booking_id = await manager.start_new_saga(x_user_id, body.seat_ids, db)

    return {"status": "PROCESSING", "booking_id": booking_id}


@router.get("/status/{booking_id}")
async def get_booking_status(booking_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await saga_manager.get_booking_status(booking_id, db)


@router.get("/history/me")
async def get_my_history(x_user_id: uuid.UUID = Header(...), db: AsyncSession = Depends(get_db)):
    return await saga_manager.get_my_history(x_user_id, db)
