import uuid
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from common.database import Base
from common.outbox.models import OutboxEvent  # noqa: F401 — registers outbox_events table


class SagaStatus(str, PyEnum):
    started = "started"
    seat_reserved = "seat_reserved"
    seat_reservation_failed = "seat_reservation_failed"
    order_created = "order_created"
    payment_pending = "payment_pending"
    payment_success = "payment_success"
    payment_failed = "payment_failed"
    completed = "completed"
    cancelled = "cancelled"


class BookingSaga(Base):
    __tablename__ = "booking_sagas"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    seat_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=False)

    status: Mapped[SagaStatus] = mapped_column(Enum(SagaStatus), default=SagaStatus.started, nullable=False)
    is_seat_sold: Mapped[bool] = mapped_column(Boolean, default=False)
    is_order_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    ticket_url: Mapped[str] = mapped_column(String(500), nullable=True)
    error_reason: Mapped[str] = mapped_column(String(255), nullable=True)
