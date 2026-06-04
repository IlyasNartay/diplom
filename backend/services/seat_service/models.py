import enum
import uuid

from sqlalchemy import Enum, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from common.database import Base
from common.outbox.models import OutboxEvent  # noqa: F401 — registers outbox_events table


class SeatStatus(str, enum.Enum):
    free = "free"
    reserved = "reserved"
    sold = "sold"


class Seat(Base):
    __tablename__ = "seats"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)

    row: Mapped[str] = mapped_column(String(10), nullable=False)
    number: Mapped[str] = mapped_column(String(10), nullable=False)

    status: Mapped[SeatStatus] = mapped_column(Enum(SeatStatus), default=SeatStatus.free, nullable=False)

    booking_id: Mapped[str | None] = mapped_column(String, nullable=True)
    price: Mapped[int] = mapped_column(Integer, default=5000, nullable=False)
