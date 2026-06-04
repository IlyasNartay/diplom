"""
apps/seats/models.py
Модель места (Seat) и статусов.
FREE → RESERVED (Redis lock, TTL) → SOLD (после оплаты)
"""
from django.db import models


class SeatStatus(models.TextChoices):
    FREE     = "FREE",     "Свободно"
    RESERVED = "RESERVED", "Забронировано"
    SOLD     = "SOLD",     "Продано"


class Seat(models.Model):
    event     = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="seats",
        verbose_name="Событие",
    )
    row       = models.PositiveSmallIntegerField("Ряд")
    number    = models.PositiveSmallIntegerField("Место")
    category  = models.CharField("Категория", max_length=50, default="standard")
    price     = models.DecimalField("Цена", max_digits=10, decimal_places=2)
    status    = models.CharField(
        "Статус",
        max_length=10,
        choices=SeatStatus.choices,
        default=SeatStatus.FREE,
        db_index=True,   # индекс для быстрого поиска свободных мест
    )

    class Meta:
        db_table = "seats"
        unique_together = ("event", "row", "number")
        indexes = [
            models.Index(fields=["event", "status"]),
        ]

    def __str__(self):
        return f"Event#{self.event_id} R{self.row}:N{self.number} [{self.status}]"
