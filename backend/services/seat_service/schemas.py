import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from services.seat_service.models import SeatStatus


class SeatResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    row: str
    number: str
    status: SeatStatus
    booking_id: Optional[str] = None
    price: int

    model_config = ConfigDict(from_attributes=True)


class GenerateSeatsRequest(BaseModel):
    rows: int
    seats_per_row: int


class GenerateSeatsResponse(BaseModel):
    message: str
    session_id: uuid.UUID
    total_created: int


class SyncSessionSeatPricesRequest(BaseModel):
    price: int = Field(ge=0)
