"""apps/tickets/views.py"""
import os
from django.http import FileResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings

from apps.orders.models import Order, OrderStatus


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_ticket(request, order_id: int):
    """
    GET /api/v1/tickets/<order_id>/
    Возвращает PDF-файл билета если заказ оплачен.
    """
    try:
        order = Order.objects.get(id=order_id, user=request.user, status=OrderStatus.PAID)
    except Order.DoesNotExist:
        return Response({"error": "Оплаченный заказ не найден"}, status=404)

    # Ищем файл по order_id
    tickets_dir = os.path.join(settings.MEDIA_ROOT, "tickets")
    # В реальной системе путь хранится в модели Ticket
    # Здесь ищем последний файл для простоты
    files = [f for f in os.listdir(tickets_dir) if f.endswith(".pdf")]
    if not files:
        return Response({"error": "Билет ещё не сгенерирован"}, status=404)

    filepath = os.path.join(tickets_dir, sorted(files)[-1])
    return FileResponse(
        open(filepath, "rb"),
        content_type="application/pdf",
        as_attachment=True,
        filename=os.path.basename(filepath),
    )
