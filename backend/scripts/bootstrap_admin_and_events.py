import asyncio
import os
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select

from common.database import create_session_factory
from services.auth_service.logic.security import get_password_hash
from services.auth_service.models import Role, User
from services.catalog_service.models import Category, City, Event, Session
from services.seat_service.logic.seat_manager import generate_seats
from services.seat_service.models import Seat


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@postgres:5432/ticketon_main_db")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@sdu.edu.kz")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "SduAdmin2026!")
ADMIN_FULL_NAME = os.getenv("ADMIN_FULL_NAME", "SDU Administrator")
DEFAULT_TZ = ZoneInfo("Asia/Almaty")


@dataclass(frozen=True)
class SessionSeed:
    start_time: str
    hall_name: str
    price: int


@dataclass(frozen=True)
class CityEventSeed:
    city_ru: str
    sessions: list[SessionSeed]


@dataclass(frozen=True)
class EventSeed:
    title: str
    description: str
    category_ru: str
    poster_url: str
    city_events: list[CityEventSeed]


CATEGORIES = [
    {"name_ru": "Фильмы", "name_en": "Movies", "name_kz": "Фильмдер"},
    {"name_ru": "Концерты", "name_en": "Concerts", "name_kz": "Концерттер"},
    {"name_ru": "Фестивали", "name_en": "Festivals", "name_kz": "Фестивальдер"},
]

CITIES = [
    {"name_ru": "Алматы", "name_en": "Almaty", "name_kz": "Алматы"},
    {"name_ru": "Астана", "name_en": "Astana", "name_kz": "Астана"},
    {"name_ru": "Шымкент", "name_en": "Shymkent", "name_kz": "Шымкент"},
    {"name_ru": "Атырау", "name_en": "Atyrau", "name_kz": "Атырау"},
]

EVENTS = [
    EventSeed(
        title="ОПАСНЫЙ ГОРОД",
        description="Триллер о преступлениях в большом городе",
        category_ru="Фильмы",
        poster_url="https://images.unsplash.com/photo-1607555509198-84b77411468d?auto=format&fit=crop&fm=jpg&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&ixlib=rb-4.1.0&q=60&w=1200",
        city_events=[
            CityEventSeed(
                city_ru="Алматы",
                sessions=[
                    SessionSeed("2026-05-01T10:00:00", "Зал А", 2500),
                    SessionSeed("2026-05-01T14:00:00", "Зал Б", 2500),
                    SessionSeed("2026-05-01T18:00:00", "Зал В", 3000),
                ],
            ),
            CityEventSeed(
                city_ru="Астана",
                sessions=[
                    SessionSeed("2026-05-01T10:00:00", "Зал 1", 2200),
                    SessionSeed("2026-05-01T14:00:00", "Зал 2", 2200),
                    SessionSeed("2026-05-01T18:00:00", "Зал 3", 2500),
                ],
            ),
            CityEventSeed(
                city_ru="Шымкент",
                sessions=[SessionSeed("2026-05-01T19:00:00", "Кинотеатр Центральный", 2000)],
            ),
        ],
    ),
    EventSeed(
        title="ЗВЁЗДНЫЕ ВОЙНЫ: НОВАЯ НАДЕЖДА",
        description="Научно-фантастический боевик",
        category_ru="Фильмы",
        poster_url="https://images.unsplash.com/photo-1462332420958-a05d1e002413?auto=format&fit=crop&fm=jpg&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&ixlib=rb-4.1.0&q=60&w=1200",
        city_events=[
            CityEventSeed(
                city_ru="Алматы",
                sessions=[
                    SessionSeed("2026-05-02T10:00:00", "Зал А", 2800),
                    SessionSeed("2026-05-02T14:00:00", "Зал Б", 2800),
                    SessionSeed("2026-05-02T18:00:00", "Зал В", 3200),
                ],
            ),
            CityEventSeed(
                city_ru="Астана",
                sessions=[
                    SessionSeed("2026-05-02T10:00:00", "Зал 1", 2500),
                    SessionSeed("2026-05-02T14:00:00", "Зал 2", 2500),
                    SessionSeed("2026-05-02T18:00:00", "Зал 3", 2800),
                ],
            ),
            CityEventSeed(
                city_ru="Атырау",
                sessions=[SessionSeed("2026-05-02T20:00:00", "Кинотеатр Премиум", 2200)],
            ),
        ],
    ),
    EventSeed(
        title="ЛЮБОВЬ В ПАРИЖЕ",
        description="Романтическая драма",
        category_ru="Фильмы",
        poster_url="https://images.unsplash.com/photo-1757435755336-f715ff8896d8?auto=format&fit=crop&fm=jpg&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&ixlib=rb-4.1.0&q=60&w=1200",
        city_events=[
            CityEventSeed(
                city_ru="Алматы",
                sessions=[
                    SessionSeed("2026-05-03T10:00:00", "Зал А", 2400),
                    SessionSeed("2026-05-03T14:00:00", "Зал Б", 2400),
                    SessionSeed("2026-05-03T18:00:00", "Зал В", 2800),
                ],
            ),
            CityEventSeed(
                city_ru="Астана",
                sessions=[
                    SessionSeed("2026-05-03T10:00:00", "Зал 1", 2200),
                    SessionSeed("2026-05-03T14:00:00", "Зал 2", 2200),
                    SessionSeed("2026-05-03T18:00:00", "Зал 3", 2500),
                ],
            ),
        ],
    ),
    EventSeed(
        title="ИНДИАНА ДЖОНС И ПОТЕРЯННЫЙ АРТЕФАКТ",
        description="Приключенческий боевик",
        category_ru="Фильмы",
        poster_url="https://images.unsplash.com/photo-1767936925063-973476cec990?auto=format&fit=crop&fm=jpg&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&ixlib=rb-4.1.0&q=60&w=1200",
        city_events=[
            CityEventSeed(
                city_ru="Алматы",
                sessions=[
                    SessionSeed("2026-05-04T10:00:00", "Зал А", 2800),
                    SessionSeed("2026-05-04T14:00:00", "Зал Б", 2800),
                    SessionSeed("2026-05-04T18:00:00", "Зал В", 3200),
                ],
            ),
            CityEventSeed(
                city_ru="Астана",
                sessions=[
                    SessionSeed("2026-05-04T10:00:00", "Зал 1", 2500),
                    SessionSeed("2026-05-04T14:00:00", "Зал 2", 2500),
                    SessionSeed("2026-05-04T18:00:00", "Зал 3", 2800),
                ],
            ),
            CityEventSeed(
                city_ru="Шымкент",
                sessions=[SessionSeed("2026-05-04T19:30:00", "Кинотеатр Центральный", 2200)],
            ),
        ],
    ),
    EventSeed(
        title="УЖАС В ЛЕСУ",
        description="Психологический триллер",
        category_ru="Фильмы",
        poster_url="https://images.unsplash.com/photo-1770736957456-d552bc016472?auto=format&fit=crop&fm=jpg&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&ixlib=rb-4.1.0&q=60&w=1200",
        city_events=[
            CityEventSeed(
                city_ru="Алматы",
                sessions=[
                    SessionSeed("2026-05-05T10:00:00", "Зал А", 2400),
                    SessionSeed("2026-05-05T14:00:00", "Зал Б", 2400),
                    SessionSeed("2026-05-05T18:00:00", "Зал В", 2800),
                ],
            ),
            CityEventSeed(
                city_ru="Астана",
                sessions=[
                    SessionSeed("2026-05-05T10:00:00", "Зал 1", 2200),
                    SessionSeed("2026-05-05T14:00:00", "Зал 2", 2200),
                    SessionSeed("2026-05-05T18:00:00", "Зал 3", 2500),
                ],
            ),
        ],
    ),
    EventSeed(
        title="КАЙРАТ НУРТАС LIVE",
        description="Концерт казахского рок-певца",
        category_ru="Концерты",
        poster_url="https://images.unsplash.com/photo-1770737639812-bd3c709da73b?auto=format&fit=crop&fm=jpg&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&ixlib=rb-4.1.0&q=60&w=1200",
        city_events=[
            CityEventSeed(
                city_ru="Алматы",
                sessions=[SessionSeed("2026-05-06T20:00:00", "Дворец культуры", 5000)],
            ),
            CityEventSeed(
                city_ru="Астана",
                sessions=[SessionSeed("2026-05-07T20:00:00", "Дворец им. Абая", 4500)],
            ),
        ],
    ),
    EventSeed(
        title="DJ SHCHK & FRIENDS EDM FESTIVAL",
        description="Электронная музыка. Топовые диджеи",
        category_ru="Концерты",
        poster_url="https://images.unsplash.com/photo-1773274157508-ddbf6074aa14?auto=format&fit=crop&fm=jpg&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&ixlib=rb-4.1.0&q=60&w=1200",
        city_events=[
            CityEventSeed(
                city_ru="Алматы",
                sessions=[SessionSeed("2026-05-08T22:00:00", "Атакент Арена", 3500)],
            ),
        ],
    ),
    EventSeed(
        title="ALMATY FOOD FEST",
        description="Международный фестиваль еды с лучшими шефами",
        category_ru="Фестивали",
        poster_url="https://images.unsplash.com/photo-1683731495404-0fae506e2717?auto=format&fit=crop&fm=jpg&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&ixlib=rb-4.1.0&q=60&w=1200",
        city_events=[
            CityEventSeed(
                city_ru="Алматы",
                sessions=[SessionSeed("2026-05-10T11:00:00", "Парк 28 панфиловцев", 1500)],
            ),
            CityEventSeed(
                city_ru="Астана",
                sessions=[SessionSeed("2026-05-11T11:00:00", "Парк Евразии", 1500)],
            ),
        ],
    ),
    EventSeed(
        title="ASTANA TECH CONFERENCE 2026",
        description="Конференция по новым технологиям и инновациям",
        category_ru="Фестивали",
        poster_url="https://images.unsplash.com/photo-1762968269894-1d7e1ce8894e?auto=format&fit=crop&fm=jpg&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&ixlib=rb-4.1.0&q=60&w=1200",
        city_events=[
            CityEventSeed(
                city_ru="Астана",
                sessions=[SessionSeed("2026-05-15T09:00:00", "Конференц-центр Expo", 2000)],
            ),
            CityEventSeed(
                city_ru="Шымкент",
                sessions=[SessionSeed("2026-05-16T09:00:00", "Hotel Meridian", 1800)],
            ),
        ],
    ),
]

SEAT_LAYOUTS = {
    "Фильмы": (6, 8),
    "Концерты": (8, 10),
    "Фестивали": (8, 10),
}


def parse_local_dt(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=DEFAULT_TZ)


async def upsert_admin(session) -> User:
    result = await session.execute(select(User).where(User.email == ADMIN_EMAIL))
    user = result.scalar_one_or_none()
    password_hash = get_password_hash(ADMIN_PASSWORD)

    if user is None:
        user = User(
            email=ADMIN_EMAIL,
            password_hash=password_hash,
            full_name=ADMIN_FULL_NAME,
            role=Role.admin,
        )
        session.add(user)
    else:
        user.password_hash = password_hash
        user.full_name = ADMIN_FULL_NAME
        user.role = Role.admin

    await session.commit()
    await session.refresh(user)
    return user


async def get_or_create_category(session, payload: dict) -> Category:
    result = await session.execute(select(Category).where(Category.name_ru == payload["name_ru"]))
    category = result.scalar_one_or_none()
    if category is None:
        category = Category(**payload, is_active=True)
        session.add(category)
    else:
        category.name_en = payload["name_en"]
        category.name_kz = payload["name_kz"]
        category.is_active = True
    await session.commit()
    await session.refresh(category)
    return category


async def get_or_create_city(session, payload: dict) -> City:
    result = await session.execute(select(City).where(City.name_ru == payload["name_ru"]))
    city = result.scalar_one_or_none()
    if city is None:
        city = City(**payload, is_active=True)
        session.add(city)
    else:
        city.name_en = payload["name_en"]
        city.name_kz = payload["name_kz"]
        city.is_active = True
    await session.commit()
    await session.refresh(city)
    return city


async def get_or_create_event(
    session, *, title: str, description: str, poster_url: str, category_id, city_id
) -> tuple[Event, bool]:
    result = await session.execute(
        select(Event).where(
            Event.title == title,
            Event.city_id == city_id,
        )
    )
    event = result.scalars().first()
    created = False
    if event is None:
        event = Event(
            title=title,
            description=description,
            poster_url=poster_url,
            category_id=category_id,
            city_id=city_id,
            is_active=True,
        )
        session.add(event)
        created = True
    else:
        event.description = description
        event.poster_url = poster_url
        event.category_id = category_id
        event.city_id = city_id
        event.is_active = True
    await session.commit()
    await session.refresh(event)
    return event, created


async def get_or_create_session(session, *, event_id, seed: SessionSeed) -> tuple[Session, bool]:
    start_time = parse_local_dt(seed.start_time)
    result = await session.execute(
        select(Session).where(
            Session.event_id == event_id,
            Session.start_time == start_time,
            Session.hall_name == seed.hall_name,
        )
    )
    session_obj = result.scalars().first()
    created = False

    if session_obj is None:
        session_obj = Session(
            event_id=event_id,
            start_time=start_time,
            hall_name=seed.hall_name,
            price=seed.price,
            is_active=True,
        )
        session.add(session_obj)
        created = True
    else:
        session_obj.price = seed.price
        session_obj.hall_name = seed.hall_name
        session_obj.start_time = start_time
        session_obj.is_active = True

    await session.commit()
    await session.refresh(session_obj)
    return session_obj, created


async def ensure_seats(session, session_id, category_ru: str) -> int:
    existing = await session.execute(select(func.count(Seat.id)).where(Seat.session_id == session_id))
    total = int(existing.scalar() or 0)
    if total > 0:
        return 0

    rows, seats_per_row = SEAT_LAYOUTS.get(category_ru, (6, 8))
    return await generate_seats(session_id, rows, seats_per_row, session)


async def main():
    session_factory = create_session_factory(DATABASE_URL)

    async with session_factory() as session:
        admin = await upsert_admin(session)

        categories = {}
        for payload in CATEGORIES:
            category = await get_or_create_category(session, payload)
            categories[category.name_ru] = category

        cities = {}
        for payload in CITIES:
            city = await get_or_create_city(session, payload)
            cities[city.name_ru] = city

        created_events = 0
        created_sessions = 0
        generated_seats = 0

        for event_seed in EVENTS:
            category = categories[event_seed.category_ru]
            for city_seed in event_seed.city_events:
                city = cities[city_seed.city_ru]
                event, created = await get_or_create_event(
                    session,
                    title=event_seed.title,
                    description=event_seed.description,
                    poster_url=event_seed.poster_url,
                    category_id=category.id,
                    city_id=city.id,
                )
                if created:
                    created_events += 1

                for session_seed in city_seed.sessions:
                    session_obj, created = await get_or_create_session(session, event_id=event.id, seed=session_seed)
                    if created:
                        created_sessions += 1
                    generated_seats += await ensure_seats(session, session_obj.id, event_seed.category_ru)

        print("Bootstrap completed successfully.")
        print(f"Admin email: {admin.email}")
        print(f"Admin password: {ADMIN_PASSWORD}")
        print(f"Created events: {created_events}")
        print(f"Created sessions: {created_sessions}")
        print(f"Generated seats: {generated_seats}")


if __name__ == "__main__":
    asyncio.run(main())
