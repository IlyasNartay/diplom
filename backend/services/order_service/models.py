import uuid

from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from common.database import Base
from common.outbox.models import OutboxEvent  # noqa: F401 — registers outbox_events table


class Order(Base):
    __tablename__ = "orders"

    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    price: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String, default="PENDING")
    error_reason: Mapped[str] = mapped_column(String(255), nullable=True)
