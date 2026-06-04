"""
apps/seats/views.py — API views для работы с местами
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Эндпоинты:
  GET  /api/v1/seats/?event_id=<id>   — список мест события
  POST /api/v1/seats/<id>/reserve/    — выбрать/заблокировать место
  POST /api/v1/seats/<id>/release/    — отменить бронь
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .services import SeatService, SeatLockError
from .serializers import SeatSerializer


@extend_schema(summary="Список мест для события")
@api_view(["GET"])
def seat_list(request):
    event_id = request.query_params.get("event_id")
    if not event_id:
        return Response({"error": "event_id обязателен"}, status=400)

    seats = SeatService.get_seats_for_event(int(event_id))
    return Response(list(seats))


@extend_schema(summary="Забронировать место (Redis lock)")
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reserve_seat(request, seat_id: int):
    """
    Ключевой endpoint: пытается атомарно заблокировать место.
    Возвращает 409 если место уже занято (race condition защита).
    """
    try:
        seat = SeatService.reserve_seat(
            seat_id=seat_id,
            user_id=request.user.id,
        )
        return Response(
            {
                "message": "Место успешно забронировано",
                "seat": SeatSerializer(seat).data,
                "lock_ttl_seconds": 300,
            },
            status=status.HTTP_200_OK,
        )

    except SeatLockError as e:
        # HTTP 409 Conflict — стандартный статус для race condition
        return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

    except Exception as e:
        return Response({"error": "Внутренняя ошибка"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(summary="Отменить бронь места")
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def release_seat(request, seat_id: int):
    SeatService.release_seat(seat_id=seat_id)
    return Response({"message": "Бронь отменена"})
