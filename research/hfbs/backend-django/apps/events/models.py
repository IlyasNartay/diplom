"""apps/events/models.py"""
from django.db import models


class Event(models.Model):
    title       = models.CharField("Название", max_length=200)
    description = models.TextField("Описание", blank=True)
    venue       = models.CharField("Место проведения", max_length=200)
    date        = models.DateTimeField("Дата события", db_index=True)
    total_seats = models.PositiveIntegerField("Всего мест", default=0)
    image_url   = models.URLField("Изображение", blank=True)
    is_active   = models.BooleanField("Активно", default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "events"
        ordering = ["date"]

    def __str__(self):
        return f"{self.title} ({self.date:%d.%m.%Y})"
