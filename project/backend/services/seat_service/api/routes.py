import uuid
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from services.seat_service.database import get_db
from services.seat_service.logic import seat_manager
from services.seat_service.schemas import (
    GenerateSeatsRequest,
    GenerateSeatsResponse,
    SeatResponse,
    SyncSessionSeatPricesRequest,
)

router = APIRouter()


@router.get("/seats/{session_id}", response_model=List[SeatResponse])
async def get_seats(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await seat_manager.get_all_seats(session_id, db)


@router.post("/admin/seats/generate/{session_id}", response_model=GenerateSeatsResponse)
async def generate_seats_endpoint(
    session_id: uuid.UUID, request: GenerateSeatsRequest, db: AsyncSession = Depends(get_db)
):
    created_count = await seat_manager.generate_seats(session_id, request.rows, request.seats_per_row, db)
    return GenerateSeatsResponse(
        message="Seats successfully generated",
        session_id=session_id,
        total_created=created_count,
    )


@router.put("/admin/seats/session/{session_id}/price")
async def sync_session_seat_prices(
    session_id: uuid.UUID, body: SyncSessionSeatPricesRequest, db: AsyncSession = Depends(get_db)
):
    updated = await seat_manager.sync_seat_prices_for_session(session_id, body.price, db)
    return {"session_id": str(session_id), "price": body.price, "seats_updated": updated}
