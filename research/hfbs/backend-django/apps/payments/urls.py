"""apps/payments/urls.py"""
from django.urls import path
from . import views

urlpatterns = [
    path("", views.process_payment, name="payment-process"),
]
