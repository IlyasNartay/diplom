"""
models/db_models.py — SQLAlchemy ORM модели для FastAPI
Те же таблицы, что и в Django, но описаны через SQLAlchemy.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Numeric, DateTime,
    Boolean, ForeignKey, UniqueConstraint, Index, Enum as SAEnum,
)
from sqlalchemy.orm import relationship
from core.database import Base


class SeatStatusEnum(str, enum.Enum):
    FREE     = "FREE"
    RESERVED = "RESERVED"
    SOLD     = "SOLD"


class OrderStatusEnum(str, enum.Enum):
    PENDING   = "PENDING"
    PAID      = "PAID"
    CANCELLED = "CANCELLED"


class User(Base):
    __tablename__ = "auth_user"  # Та же таблица, что создаёт Django

    id           = Column(Integer, primary_key=True)
    username     = Column(String(150), unique=True, nullable=False)
    email        = Column(String(254), unique=True)
    password     = Column(String(128), nullable=False)
    is_active    = Column(Boolean, default=True)
    date_joined  = Column(DateTime, default=datetime.utcnow)


class Event(Base):
    __tablename__ = "events"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(200), nullable=False)
    description = Column(Text, default="")
    venue       = Column(String(200))
    date        = Column(DateTime, index=True)
    total_seats = Column(Integer, default=0)
    image_url   = Column(String(500), default="")
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    seats       = relationship("Seat", back_populates="event")


class Seat(Base):
    __tablename__ = "seats"

    id       = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    row      = Column(Integer, nullable=False)
    number   = Column(Integer, nullable=False)
    category = Column(String(50), default="standard")
    price    = Column(Numeric(10, 2), nullable=False)
    status   = Column(String(10), default=SeatStatusEnum.FREE, index=True)

    event    = relationship("Event", back_populates="seats")
    order    = relationship("Order", back_populates="seat", uselist=False)

    __table_args__ = (
        UniqueConstraint("event_id", "row", "number"),
        Index("ix_seats_event_status", "event_id", "status"),
    )


class Order(Base):
    __tablename__ = "orders"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("auth_user.id"), nullable=False)
    seat_id    = Column(Integer, ForeignKey("seats.id"), nullable=False)
    amount     = Column(Numeric(10, 2), nullable=False)
    status     = Column(String(10), default=OrderStatusEnum.PENDING, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    seat       = relationship("Seat", back_populates="order")
    user       = relationship("User")
