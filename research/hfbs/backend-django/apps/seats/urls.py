"""apps/seats/urls.py"""
from django.urls import path
from . import views

urlpatterns = [
    path("",                       views.seat_list,    name="seat-list"),
    path("<int:seat_id>/reserve/", views.reserve_seat, name="seat-reserve"),
    path("<int:seat_id>/release/", views.release_seat, name="seat-release"),
]
