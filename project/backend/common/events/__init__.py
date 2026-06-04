from typing import List, Literal
from uuid import UUID

from pydantic import BaseModel

# --- SEAT EVENTS ---


class SeatReservedEvent(BaseModel):
    type: Literal["SeatReserved"] = "SeatReserved"
    booking_id: UUID
    seat_ids: List[UUID]
    total_price: int


class SeatReservationFailedEvent(BaseModel):
    type: Literal["SeatReservationFailed"] = "SeatReservationFailed"
    booking_id: UUID
    seat_ids: List[UUID]
    reason: str  # "ALREADY_BOOKED", "NOT_FOUND"


class SeatSoldEvent(BaseModel):
    type: Literal["SeatSold"] = "SeatSold"
    booking_id: UUID
    seat_ids: List[UUID]


class SeatReleasedEvent(BaseModel):
    type: Literal["SeatReleased"] = "SeatReleased"
    booking_id: UUID
    seat_ids: List[UUID]


# --- ORDER EVENTS ---


class OrderCreatedEvent(BaseModel):
    type: Literal["OrderCreated"] = "OrderCreated"
    booking_id: UUID
    order_id: UUID
    status: str
    price: int


class OrderCompletedEvent(BaseModel):
    type: Literal["OrderCompleted"] = "OrderCompleted"
    booking_id: UUID
    order_id: UUID


class OrderCancelledEvent(BaseModel):
    type: Literal["OrderCancelled"] = "OrderCancelled"
    booking_id: UUID
    order_id: UUID
    reason: str = "Unknown reason"


# --- PAYMENT EVENTS ---


class PaymentSucceededEvent(BaseModel):
    type: Literal["PaymentSucceeded"] = "PaymentSucceeded"
    booking_id: UUID
    order_id: UUID
    payment_id: UUID


class PaymentFailedEvent(BaseModel):
    type: Literal["PaymentFailed"] = "PaymentFailed"
    booking_id: UUID
    order_id: UUID
    reason: str


# --- TICKET EVENTS ---


class TicketIssuedEvent(BaseModel):
    type: Literal["TicketIssued"] = "TicketIssued"
    booking_id: UUID
    ticket_urls: List[str]
