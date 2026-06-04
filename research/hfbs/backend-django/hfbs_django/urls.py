"""
HFBS Django — корневые URL
Все API-маршруты начинаются с /api/v1/
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),

    # ── Auth ────────────────────────────────────────────────
    path("api/v1/auth/token/", TokenObtainPairView.as_view(), name="token_obtain"),
    path("api/v1/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # ── Business routes ─────────────────────────────────────
    path("api/v1/events/",   include("apps.events.urls")),
    path("api/v1/seats/",    include("apps.seats.urls")),
    path("api/v1/orders/",   include("apps.orders.urls")),
    path("api/v1/payments/", include("apps.payments.urls")),
    path("api/v1/tickets/",  include("apps.tickets.urls")),

    # ── OpenAPI Docs ─────────────────────────────────────────
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/",   SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
