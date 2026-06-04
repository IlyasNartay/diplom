"""apps/orders/urls.py"""
from django.urls import path
from . import views

urlpatterns = [
    path("",               views.create_order, name="order-create"),
    path("<int:order_id>/", views.order_detail, name="order-detail"),
]
