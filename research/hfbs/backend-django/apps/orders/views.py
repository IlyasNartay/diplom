"""apps/orders/views.py"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

from .models import Order, OrderStatus
from apps.seats.models import Seat, SeatStatus
from apps.analytics.event_service import EventService


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_order(request):
    """
    POST /api/v1/orders/
    Body: { "seat_id": 5 }
    Создаёт заказ для уже RESERVED места.
    """
    seat_id = request.data.get("seat_id")
    if not seat_id:
        return Response({"error": "seat_id обязателен"}, status=400)

    try:
        with transaction.atomic():
            seat = Seat.objects.select_for_update().get(
                id=seat_id,
                status=SeatStatus.RESERVED,
            )
            order = Order.objects.create(
                user=request.user,
                seat=seat,
                amount=seat.price,
                status=OrderStatus.PENDING,
            )

        EventService.publish("order", {
            "type":     "ORDER_CREATED",
            "order_id": order.id,
            "user_id":  request.user.id,
            "seat_id":  seat_id,
            "amount":   str(order.amount),
        })

        return Response({
            "order_id": order.id,
            "amount":   str(order.amount),
            "status":   order.status,
        }, status=status.HTTP_201_CREATED)

    except Seat.DoesNotExist:
        return Response(
            {"error": "Место не найдено или не забронировано"},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def order_detail(request, order_id: int):
    try:
        order = Order.objects.select_related("seat", "seat__event").get(
            id=order_id, user=request.user
        )
        return Response({
            "order_id":   order.id,
            "status":     order.status,
            "amount":     str(order.amount),
            "seat":       {"row": order.seat.row, "number": order.seat.number},
            "event":      order.seat.event.title,
            "created_at": order.created_at,
        })
    except Order.DoesNotExist:
        return Response({"error": "Заказ не найден"}, status=404)
