from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class BookingStatus(BaseModel):
    booking_id: UUID
    status: str
    seat_ids: List[UUID]
    ticket_url: str | None = None
    error_reason: str | None = None
    event_title: str | None = None
    event_is_active: bool | None = None
    session_has_passed: bool | None = None


# --- SEAT COMMANDS ---
class ReserveSeatCommand(BaseModel):
    type: Literal["ReserveSeat"] = "ReserveSeat"
    booking_id: UUID
    seat_ids: List[UUID]
    user_id: UUID


class ConfirmSeatCommand(BaseModel):
    type: Literal["ConfirmSeat"] = "ConfirmSeat"
    booking_id: UUID
    seat_ids: List[UUID]


class ReleaseSeatCommand(BaseModel):
    type: Literal["ReleaseSeat"] = "ReleaseSeat"
    booking_id: UUID
    seat_ids: List[UUID]


# --- ORDER COMMANDS ---
class CreateOrderCommand(BaseModel):
    type: Literal["CreateOrder"] = "CreateOrder"
    booking_id: UUID
    seat_ids: List[UUID]
    user_id: UUID
    price: int


class CompleteOrderCommand(BaseModel):
    type: Literal["CompleteOrder"] = "CompleteOrder"
    booking_id: UUID
    order_id: UUID


class CancelOrderCommand(BaseModel):
    type: Literal["CancelOrder"] = "CancelOrder"
    booking_id: UUID
    order_id: Optional[UUID] = None
    reason: str = "Unknown reason"


# --- PAYMENT COMMANDS ---
class CreatePaymentCommand(BaseModel):
    type: Literal["CreatePayment"] = "CreatePayment"
    booking_id: UUID
    order_id: UUID
    amount: int
    user_id: UUID


# --- TICKET COMMANDS ---
class GenerateTicketCommand(BaseModel):
    type: Literal["GenerateTicket"] = "GenerateTicket"
    booking_id: UUID
    order_id: UUID
    user_id: UUID
    seat_ids: List[UUID]
