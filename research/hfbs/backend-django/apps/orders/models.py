"""
apps/orders/models.py — модель заказа
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class OrderStatus(models.TextChoices):
    PENDING   = "PENDING",   "Ожидает оплаты"
    PAID      = "PAID",      "Оплачен"
    CANCELLED = "CANCELLED", "Отменён"


class Order(models.Model):
    user      = models.ForeignKey(User, on_delete=models.PROTECT, related_name="orders")
    seat      = models.OneToOneField("seats.Seat", on_delete=models.PROTECT, related_name="order")
    amount    = models.DecimalField("Сумма", max_digits=10, decimal_places=2)
    status    = models.CharField(
        max_length=10, choices=OrderStatus.choices, default=OrderStatus.PENDING, db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"

    def __str__(self):
        return f"Order#{self.id} [{self.status}] ${self.amount}"
