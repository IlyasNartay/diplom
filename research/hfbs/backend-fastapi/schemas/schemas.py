"""
schemas/schemas.py — Pydantic v2 схемы для валидации запросов/ответов
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, EmailStr


# ── Auth ─────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str


# ── Events ───────────────────────────────────────────────────

class EventOut(BaseModel):
    id:          int
    title:       str
    description: str
    venue:       str
    date:        datetime
    total_seats: int
    image_url:   str

    model_config = {"from_attributes": True}


# ── Seats ────────────────────────────────────────────────────

class SeatOut(BaseModel):
    id:       int
    row:      int
    number:   int
    category: str
    price:    Decimal
    status:   str

    model_config = {"from_attributes": True}

class ReserveSeatRequest(BaseModel):
    pass  # seat_id передаётся в path параметре

class ReserveSeatResponse(BaseModel):
    message:          str
    seat:             SeatOut
    lock_ttl_seconds: int


# ── Orders ───────────────────────────────────────────────────

class CreateOrderRequest(BaseModel):
    seat_id: int

class OrderOut(BaseModel):
    order_id:   int
    amount:     Decimal
    status:     str
    created_at: Optional[datetime] = None


# ── Payments ─────────────────────────────────────────────────

class PaymentRequest(BaseModel):
    order_id:   int
    card_token: str = "tok_mock_visa"

class PaymentResponse(BaseModel):
    payment_id: str
    order_id:   int
    ticket_url: str


# ── Error ────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
