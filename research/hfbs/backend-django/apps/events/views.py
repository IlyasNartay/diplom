"""apps/events/views.py"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Event
from .serializers import EventSerializer


@api_view(["GET"])
def event_list(request):
    events = Event.objects.filter(is_active=True).values(
        "id", "title", "description", "venue", "date", "total_seats", "image_url"
    )
    return Response(list(events))


@api_view(["GET"])
def event_detail(request, pk: int):
    try:
        event = Event.objects.get(pk=pk, is_active=True)
        return Response(EventSerializer(event).data)
    except Event.DoesNotExist:
        return Response({"error": "Событие не найдено"}, status=404)
