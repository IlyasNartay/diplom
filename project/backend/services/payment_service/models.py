import uuid

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from common.database import Base
from common.outbox.models import OutboxEvent  # noqa: F401 — registers outbox_events table


class Payment(Base):
    __tablename__ = "payments"

    booking_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False)
    order_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))

    amount: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String, default="PENDING")  # PENDING, SUCCESS, FAILED
    error_reason: Mapped[str] = mapped_column(String(255), nullable=True)


class SavedCard(Base):
    """Сохранённая карта пользователя.

    ВНИМАНИЕ (для прод-окружения): хранение PAN/CVV вне PCI-DSS-сертифицированного
    хранилища недопустимо. В реальном проекте здесь хранится только token провайдера,
    last4, brand, exp_*. Эта реализация — упрощение для учебных целей.
    """

    __tablename__ = "saved_cards"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)

    brand: Mapped[str] = mapped_column(String(20), nullable=False)
    last4: Mapped[str] = mapped_column(String(4), nullable=False)
    pan_full: Mapped[str] = mapped_column(String(19), nullable=False)
    exp_month: Mapped[int] = mapped_column(Integer, nullable=False)
    exp_year: Mapped[int] = mapped_column(Integer, nullable=False)
    cvv: Mapped[str] = mapped_column(String(4), nullable=False)
    holder_name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
