"""apps/payments/views.py"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .services import PaymentService, PaymentError


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def process_payment(request):
    """
    POST /api/v1/payments/
    Body: { "order_id": 1, "card_token": "tok_mock_visa" }
    """
    order_id   = request.data.get("order_id")
    card_token = request.data.get("card_token", "tok_mock")

    if not order_id:
        return Response({"error": "order_id обязателен"}, status=400)

    try:
        result = PaymentService.process_payment(
            order_id=int(order_id),
            card_token=card_token,
        )
        return Response(result, status=status.HTTP_200_OK)
    except PaymentError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        return Response({"error": "Ошибка обработки платежа"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
