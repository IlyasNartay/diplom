import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from common.database import Base
from common.outbox.models import OutboxEvent  # noqa: F401 — registers outbox_events table


class Ticket(Base):
    __tablename__ = "tickets"

    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    ticket_url: Mapped[str] = mapped_column(String, nullable=False)
