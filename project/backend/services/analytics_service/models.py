import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from common.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    topic: Mapped[str] = mapped_column(String(50), index=True)

    event_type: Mapped[str] = mapped_column(String(100), index=True)

    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=True)

    correlation_id: Mapped[str] = mapped_column(String(100), index=True, nullable=True)

    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
