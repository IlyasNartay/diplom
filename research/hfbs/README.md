# ⚡ High-Frequency Booking System (HFBS)

> **Дипломный проект** — система продажи билетов с защитой от race conditions, Redis-блокировками, event-driven архитектурой и двумя вариантами backend (Django sync vs FastAPI async).

---

## 📐 Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React)                         │
│          http://localhost:3000                               │
│  EventsPage → SeatsPage → PaymentPage → TicketPage          │
└──────────────┬──────────────────┬───────────────────────────┘
               │                  │
    ┌──────────▼───────┐  ┌───────▼──────────┐
    │  Django (sync)   │  │  FastAPI (async)  │
    │  :8000           │  │  :8001            │
    │  DRF + simplejwt │  │  Pydantic + OAuth2│
    │  psycopg2 (sync) │  │  asyncpg (async)  │
    │  django-redis    │  │  redis.asyncio    │
    │  kafka-python    │  │  aiokafka         │
    └──────────┬───────┘  └───────┬──────────┘
               │                  │
    ┌──────────▼──────────────────▼──────────┐
    │           SHARED INFRASTRUCTURE         │
    │                                         │
    │  PostgreSQL :5432  Redis :6379          │
    │  Kafka :9092       Zookeeper :2181      │
    └─────────────────────────────────────────┘
```

### Поток бронирования

```
User selects seat
      │
      ▼
SeatService.reserve_seat()
      │
      ├─→ Redis SET NX EX 300 ──→ FAIL (409 Conflict — Race condition!)
      │
      └─→ SUCCESS: Redis lock acquired
            │
            ▼
       PostgreSQL: Seat.status = RESERVED (SELECT FOR UPDATE)
            │
            ▼
       OrderService.create_order()
            │
            ▼
       PaymentService.process_payment()  ← mock payment gateway
            │
            ├─→ PostgreSQL TX: Order=PAID + Seat=SOLD (atomic)
            │
            └─→ TicketService.generate_pdf()
                      │
                      └─→ EventService.publish() → Kafka topics
```

---

## 🚀 Быстрый старт

### 1. Клонирование и запуск

```bash
git clone <repo>
cd hfbs

# Запуск всей инфраструктуры
docker compose up -d postgres redis zookeeper kafka

# Запуск backend-ов
docker compose up -d django fastapi

# Запуск frontend
docker compose up -d frontend
```

### 2. Инициализация данных

```bash
# Применяем Django миграции
docker exec hfbs_django python manage.py migrate

# Заполняем тестовыми данными (события + места + пользователи)
docker exec hfbs_django python manage.py shell < seed.py

# Создаём таблицы для FastAPI (использует те же таблицы)
docker exec hfbs_fastapi python alembic_init.py
```

### 3. Открываем приложение

| Сервис | URL |
|--------|-----|
| Frontend | http://localhost:3000 |
| Django API | http://localhost:8000/api/docs/ |
| FastAPI docs | http://localhost:8001/docs |
| Django Admin | http://localhost:8000/admin/ |

**Тестовые пользователи:**
- `admin / admin123` (суперпользователь)
- `testuser / testpass123` (обычный пользователь)

---

## 📁 Структура проекта

```
hfbs/
├── docker-compose.yml              # Оркестрация всех сервисов
│
├── frontend/                       # React + Vite (порт 3000)
│   ├── src/
│   │   ├── App.jsx                 # Роутинг
│   │   ├── components/
│   │   │   └── Navbar.jsx          # Навигация + переключатель backend
│   │   ├── pages/
│   │   │   ├── EventsPage.jsx      # Список событий
│   │   │   ├── SeatsPage.jsx       # Карта мест с блокировками
│   │   │   ├── PaymentPage.jsx     # Форма оплаты
│   │   │   ├── TicketPage.jsx      # Просмотр и скачивание билета
│   │   │   └── LoginPage.jsx       # Авторизация
│   │   ├── services/
│   │   │   └── api.js              # ★ Единый API-клиент (Django + FastAPI)
│   │   └── store/
│   │       └── useStore.js         # Zustand state management
│   └── package.json
│
├── backend-django/                 # Django 4.2 (sync, порт 8000)
│   ├── hfbs_django/
│   │   ├── settings.py             # ★ Redis cache, JWT, CORS, throttling
│   │   └── urls.py                 # Корневые маршруты
│   ├── apps/
│   │   ├── events/                 # Управление событиями
│   │   ├── seats/
│   │   │   ├── models.py           # Seat model (FREE→RESERVED→SOLD)
│   │   │   ├── services.py         # ★ SeatService — Redis lock (sync)
│   │   │   └── views.py            # API views с 409 handling
│   │   ├── orders/                 # OrderService
│   │   ├── payments/
│   │   │   └── services.py         # ★ PaymentService (atomic transaction)
│   │   ├── tickets/
│   │   │   └── services.py         # ★ PDF генерация (ReportLab)
│   │   └── analytics/
│   │       └── event_service.py    # ★ EventService → Kafka (sync)
│   └── seed.py                     # Тестовые данные
│
├── backend-fastapi/                # FastAPI (async, порт 8001)
│   ├── main.py                     # ★ Lifespan, routers, CORS
│   ├── core/
│   │   ├── config.py               # pydantic-settings конфигурация
│   │   ├── database.py             # ★ AsyncSession + asyncpg
│   │   ├── redis.py                # ★ redis.asyncio client
│   │   └── security.py            # JWT (jose)
│   ├── models/
│   │   └── db_models.py            # SQLAlchemy ORM модели
│   ├── schemas/
│   │   └── schemas.py              # Pydantic v2 схемы
│   ├── services/
│   │   ├── seat_service.py         # ★ AsyncSeatService — Redis SET NX (async)
│   │   ├── payment_service.py      # AsyncPaymentService
│   │   ├── ticket_service.py       # AsyncTicketService (run_in_executor)
│   │   └── event_service.py        # ★ AsyncEventService → aiokafka
│   └── routers/
│       ├── auth.py / events.py / seats.py
│       ├── orders.py / payments.py / tickets.py
│
└── infrastructure/
    └── scripts/
        ├── init.sql                # PostgreSQL init
        └── locustfile.py           # ★ Нагрузочный тест
```

---

## 🔑 Ключевые концепции (для диплома)

### 1. Защита от Race Conditions

```
Без блокировки (плохо):
  User A: SELECT seat WHERE status=FREE → OK
  User B: SELECT seat WHERE status=FREE → OK  ← одновременно!
  User A: UPDATE seat SET status=RESERVED     ← оба успевают
  User B: UPDATE seat SET status=RESERVED     ← двойная продажа!

С Redis SET NX (правильно):
  User A: SET seat_lock:5 userA NX EX 300 → OK (1)
  User B: SET seat_lock:5 userB NX EX 300 → NIL (0) → HTTP 409
  User A: SELECT FOR UPDATE + UPDATE status=RESERVED
```

### 2. Django vs FastAPI (sync vs async)

| Аспект | Django (sync) | FastAPI (async) |
|--------|--------------|-----------------|
| Обработка запросов | Thread per request | Event loop, coroutines |
| БД-драйвер | psycopg2 (блокирует поток) | asyncpg (не блокирует) |
| Redis-клиент | django-redis (sync) | redis.asyncio (await) |
| Kafka producer | kafka-python (sync) | aiokafka (await) |
| RPS при I/O-нагрузке | ~300-500 | ~1000-3000 |
| Потребление памяти | Выше (потоки) | Ниже (корутины) |

### 3. Event-Driven Architecture

Каждый сервис публикует события в Kafka-топики:
```
SeatService   → seat.events    { type: SEAT_RESERVED, seat_id, user_id }
OrderService  → order.events   { type: ORDER_CREATED, order_id, amount }
PaymentService→ payment.events { type: PAYMENT_SUCCESS, payment_id }
TicketService → ticket.events  { type: TICKET_GENERATED, ticket_id }
```

---

## 🧪 Нагрузочное тестирование

```bash
pip install locust

# Тест Django
locust -f infrastructure/scripts/locustfile.py \
  --host=http://localhost:8000 \
  --users=100 --spawn-rate=10 --run-time=60s --headless

# Тест FastAPI
locust -f infrastructure/scripts/locustfile.py \
  --host=http://localhost:8001 \
  --users=100 --spawn-rate=10 --run-time=60s --headless
```

**Метрики для диплома:**
- RPS (requests per second) — запросов в секунду
- P95 latency — 95-й перцентиль времени ответа
- Количество 409 ошибок — protected race conditions
- CPU и RAM потребление

---

## 🔌 API Endpoints (идентичны для Django и FastAPI)

```
POST /api/v1/auth/token/         — получить JWT токен
POST /api/v1/auth/register/      — регистрация

GET  /api/v1/events/             — список событий
GET  /api/v1/events/{id}/        — детали события

GET  /api/v1/seats/?event_id=N   — места события
POST /api/v1/seats/{id}/reserve/ — ★ Redis-блокировка места → 200 | 409
POST /api/v1/seats/{id}/release/ — отменить бронь

POST /api/v1/orders/             — создать заказ
GET  /api/v1/orders/{id}/        — детали заказа

POST /api/v1/payments/           — ★ обработать платёж + PDF
GET  /api/v1/tickets/{order_id}/ — скачать PDF билет
```

---

## 📊 Для дипломной работы

### Тезисы сравнения

1. **Производительность**: FastAPI показывает превосходство при I/O-bound нагрузке благодаря event loop
2. **Защита данных**: Оба backend одинаково защищены от race conditions (Redis SET NX + SELECT FOR UPDATE)
3. **Масштабируемость**: FastAPI не требует увеличения потоков при росте нагрузки
4. **Простота разработки**: Django имеет более богатую экосистему (Admin, ORM, миграции)
5. **Event-driven**: Kafka обеспечивает loose coupling между сервисами

### Диаграмма последовательности

```
Client → Frontend → [Django|FastAPI] → Redis → PostgreSQL → Kafka
  1. GET /events/                      →         (read)
  2. POST /seats/N/reserve/   → SET NX → UPDATE status=RESERVED
  3. POST /orders/                     →         INSERT order
  4. POST /payments/          → DEL    → UPDATE PAID+SOLD → PDF → PUBLISH
  5. GET /tickets/N/                   → (read PDF)
```

---

## 🛠 Разработка без Docker

```bash
# PostgreSQL и Redis должны быть запущены локально

# Django
cd backend-django
pip install -r requirements.txt
cp .env.example .env   # настройте DATABASE_URL, REDIS_URL
python manage.py migrate
python manage.py runserver 8000

# FastAPI
cd backend-fastapi
pip install -r requirements.txt
python alembic_init.py
uvicorn main:app --port 8001 --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## 📝 Технологический стек

| Компонент | Технология | Назначение |
|-----------|-----------|------------|
| Frontend | React 18 + Vite + Zustand | SPA, state management |
| Backend 1 | Django 4.2 + DRF | Sync REST API |
| Backend 2 | FastAPI + SQLAlchemy async | Async REST API |
| Auth | JWT (simplejwt / jose) | Аутентификация |
| Cache/Lock | Redis 7 | Блокировки мест |
| Database | PostgreSQL 16 | Основное хранилище |
| Messaging | Apache Kafka | Event-driven шина |
| PDF | ReportLab | Генерация билетов |
| Load Test | Locust | Нагрузочное тестирование |
| DevOps | Docker Compose | Оркестрация |
