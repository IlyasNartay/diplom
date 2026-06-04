"""apps/seats/serializers.py"""
from rest_framework import serializers
from .models import Seat


class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ["id", "row", "number", "category", "price", "status"]
