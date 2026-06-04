"""
seed.py — Скрипт для заполнения тестовыми данными
Запуск:
  docker exec hfbs_django python manage.py shell < seed.py
  # или
  docker exec hfbs_django python manage.py shell -c "exec(open('seed.py').read())"
"""
from django.utils import timezone
from datetime import timedelta
from apps.events.models import Event
from apps.seats.models import Seat
from django.contrib.auth import get_user_model

User = get_user_model()

# ── Суперпользователь ──────────────────────────────────────
user, created = User.objects.get_or_create(
    username='admin',
    defaults={'email': 'admin@hfbs.dev', 'is_staff': True, 'is_superuser': True}
)
if created:
    user.set_password('admin123')
    user.save()
    print("✅ Admin user created: admin / admin123")

# Тестовый пользователь
test_user, _ = User.objects.get_or_create(
    username='testuser',
    defaults={'email': 'test@hfbs.dev'}
)
test_user.set_password('testpass123')
test_user.save()
print("✅ Test user: testuser / testpass123")

# ── События ────────────────────────────────────────────────
events_data = [
    {
        "title": "Django vs FastAPI: Battle of Backends",
        "description": "Эпическое сравнение синхронного и асинхронного Python на высокой нагрузке. Узнайте, когда выбрать Django, а когда FastAPI.",
        "venue": "Techno Arena, Москва",
        "date": timezone.now() + timedelta(days=7),
        "total_seats": 50,
    },
    {
        "title": "Redis Internals Deep Dive",
        "description": "Как работают блокировки, TTL, Pub/Sub и Streams в Redis. Практические паттерны для высоконагруженных систем.",
        "venue": "Cloud Hall, Санкт-Петербург",
        "date": timezone.now() + timedelta(days=14),
        "total_seats": 30,
    },
    {
        "title": "Kafka Streams in Production",
        "description": "Event-driven архитектура в реальных проектах. От монолита к микросервисам через Kafka.",
        "venue": "Event Center, Казань",
        "date": timezone.now() + timedelta(days=21),
        "total_seats": 40,
    },
]

for ed in events_data:
    total = ed.pop("total_seats")
    event, created = Event.objects.get_or_create(title=ed["title"], defaults={**ed, "total_seats": total})
    if created:
        # Создаём места: 5 рядов по 10 мест
        seats = []
        categories = {1: 'vip', 2: 'premium', 3: 'standard', 4: 'standard', 5: 'economy'}
        prices = {1: 150, 2: 100, 3: 70, 4: 70, 5: 50}
        for row in range(1, 6):
            for num in range(1, 11):
                seats.append(Seat(
                    event=event,
                    row=row,
                    number=num,
                    category=categories[row],
                    price=prices[row],
                ))
        Seat.objects.bulk_create(seats)
        print(f"✅ Event created: '{event.title}' with {len(seats)} seats")
    else:
        print(f"ℹ️  Event exists: '{event.title}'")

print("\n🎉 Seed completed! Open http://localhost:3000")
