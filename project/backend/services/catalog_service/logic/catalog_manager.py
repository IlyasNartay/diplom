import logging
import uuid

import httpx
from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload, with_loader_criteria

from common.custom_logger import get_correlation_id
from common.errors import CommunicationError, NotFoundError
from services.catalog_service.config import settings
from services.catalog_service.models import Category, City, Event, Session
from services.catalog_service.schemas import (
    CategoryCreate,
    CategoryUpdate,
    CityCreate,
    CityUpdate,
    EventCreate,
    EventUpdate,
    SessionCreate,
    SessionUpdate,
)

logger = logging.getLogger(__name__)


async def _sync_seat_prices_for_session(session_id: uuid.UUID, price: int) -> None:
    url = f"{settings.SEAT_SERVICE_URL.rstrip('/')}/api/admin/seats/session/{session_id}/price"
    headers: dict[str, str] = {}
    corr = get_correlation_id()
    if corr:
        headers["X-Request-ID"] = corr
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.put(url, json={"price": price}, headers=headers, timeout=15.0)
    except httpx.RequestError as exc:
        logger.error("Seat service unreachable for price sync: %s", exc)
        raise CommunicationError() from exc
    if resp.status_code != 200:
        logger.error("Seat price sync failed: %s %s", resp.status_code, resp.text)
        raise CommunicationError()


class CatalogManager:
    @staticmethod
    def _events_base_query():
        return (
            select(Event)
            .where(Event.is_active == True)  # noqa: E712
            .options(
                selectinload(Event.category),
                selectinload(Event.city),
                selectinload(Event.sessions),
                with_loader_criteria(Session, Session.is_active == True, include_aliases=True),  # noqa: E712
            )
        )

    @staticmethod
    async def list_events(
        db,
        category_id: uuid.UUID | None = None,
        city_id: uuid.UUID | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> tuple[list[Event], int]:
        if city_id is not None:
            city_res = await db.execute(
                select(City).where(City.id == city_id, City.is_active == True)  # noqa: E712
            )
            if not city_res.scalar_one_or_none():
                raise NotFoundError("City not found")

        if category_id is not None:
            cat_res = await db.execute(
                select(Category).where(Category.id == category_id, Category.is_active == True)  # noqa: E712
            )
            if not cat_res.scalar_one_or_none():
                raise NotFoundError("Category not found")

        base = select(Event.id).where(Event.is_active == True)  # noqa: E712
        if category_id is not None:
            base = base.where(Event.category_id == category_id)
        if city_id is not None:
            base = base.where(Event.city_id == city_id)

        total = await db.execute(select(func.count()).select_from(base.subquery()))
        total_count = int(total.scalar() or 0)

        query = CatalogManager._events_base_query().order_by(Event.title.asc())
        if category_id is not None:
            query = query.where(Event.category_id == category_id)
        if city_id is not None:
            query = query.where(Event.city_id == city_id)
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)

        result = await db.execute(query)
        return result.scalars().all(), total_count

    @staticmethod
    async def get_all_sessions(db):
        result = await db.execute(
            select(Session).where(Session.is_active == True).order_by(Session.start_time.asc())  # noqa: E712
        )
        return result.scalars().all()

    @staticmethod
    async def get_sessions_by_event_id(event_id: uuid.UUID, db):
        result = await db.execute(
            select(Session)
            .where(Session.event_id == event_id, Session.is_active == True)  # noqa: E712
            .order_by(Session.start_time.asc())
        )
        return result.scalars().all()

    @staticmethod
    async def create_event(data: EventCreate, db):
        new_event = Event(
            title=data.title,
            description=data.description,
            poster_url=data.poster_url,
            video_url=data.video_url,
            category_id=data.category_id,
            city_id=data.city_id,
        )
        db.add(new_event)
        await db.commit()
        await db.refresh(new_event)
        return await CatalogManager.get_event_by_id(new_event.id, db)

    @staticmethod
    async def get_event_by_id(event_id: uuid.UUID, db, include_inactive: bool = False):
        query = (
            select(Event)
            .where(Event.id == event_id)
            .options(
                selectinload(Event.category),
                selectinload(Event.city),
                selectinload(Event.sessions),
                with_loader_criteria(Session, Session.is_active == True, include_aliases=True),  # noqa: E712
            )
        )
        if not include_inactive:
            query = query.where(Event.is_active == True)  # noqa: E712
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_events(db):
        query = CatalogManager._events_base_query()
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_events_by_category_id(category_id: uuid.UUID, db):
        cat = await db.execute(
            select(Category).where(Category.id == category_id, Category.is_active == True)  # noqa: E712
        )
        if not cat.scalar_one_or_none():
            raise NotFoundError("Category not found")

        query = (
            select(Event)
            .where(Event.category_id == category_id, Event.is_active == True)  # noqa: E712
            .options(
                selectinload(Event.category),
                selectinload(Event.city),
                selectinload(Event.sessions),
                with_loader_criteria(Session, Session.is_active == True, include_aliases=True),  # noqa: E712
            )
            .order_by(Event.title.asc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_events_by_city_id(city_id: uuid.UUID, db):
        city_res = await db.execute(
            select(City).where(City.id == city_id, City.is_active == True)  # noqa: E712
        )
        if not city_res.scalar_one_or_none():
            raise NotFoundError("City not found")

        query = (
            select(Event)
            .where(Event.city_id == city_id, Event.is_active == True)  # noqa: E712
            .options(
                selectinload(Event.category),
                selectinload(Event.city),
                selectinload(Event.sessions),
                with_loader_criteria(Session, Session.is_active == True, include_aliases=True),  # noqa: E712
            )
            .order_by(Event.title.asc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_events_by_city_and_category_id(city_id: uuid.UUID, category_id: uuid.UUID, db):
        city_res = await db.execute(
            select(City).where(City.id == city_id, City.is_active == True)  # noqa: E712
        )
        if not city_res.scalar_one_or_none():
            raise NotFoundError("City not found")

        cat_res = await db.execute(
            select(Category).where(Category.id == category_id, Category.is_active == True)  # noqa: E712
        )
        if not cat_res.scalar_one_or_none():
            raise NotFoundError("Category not found")

        query = (
            select(Event)
            .where(
                Event.city_id == city_id,
                Event.category_id == category_id,
                Event.is_active == True,  # noqa: E712
            )
            .options(
                selectinload(Event.category),
                selectinload(Event.city),
                selectinload(Event.sessions),
                with_loader_criteria(Session, Session.is_active == True, include_aliases=True),  # noqa: E712
            )
            .order_by(Event.title.asc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create_session(event_id: uuid.UUID, data: SessionCreate, db):
        event = await CatalogManager.get_event_by_id(event_id, db, include_inactive=True)
        if not event or not event.is_active:
            raise NotFoundError("Event not found")
        new_session = Session(event_id=event_id, start_time=data.start_time, hall_name=data.hall_name, price=data.price)
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        return new_session

    @staticmethod
    async def update_event(event_id: uuid.UUID, data: EventUpdate, db):
        result = await db.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one_or_none()
        if not event or not event.is_active:
            raise NotFoundError("Event not found")

        if data.category_id is not None:
            category_result = await db.execute(
                select(Category).where(Category.id == data.category_id, Category.is_active == True)  # noqa: E712
            )
            category = category_result.scalar_one_or_none()
            if not category:
                raise NotFoundError("Category not found")
            event.category_id = data.category_id

        if data.city_id is not None:
            city_result = await db.execute(
                select(City).where(City.id == data.city_id, City.is_active == True)  # noqa: E712
            )
            city = city_result.scalar_one_or_none()
            if not city:
                raise NotFoundError("City not found")
            event.city_id = data.city_id

        if data.title is not None:
            event.title = data.title
        if "description" in data.model_fields_set:
            event.description = data.description
        if data.poster_url is not None:
            event.poster_url = data.poster_url
        if "video_url" in data.model_fields_set:
            event.video_url = data.video_url or None

        await db.commit()
        await db.refresh(event)
        return await CatalogManager.get_event_by_id(event.id, db, include_inactive=True)

    @staticmethod
    async def replace_event_poster_url(
        event_id: uuid.UUID, new_poster_url: str, db
    ) -> tuple[Event, str | None]:
        result = await db.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one_or_none()
        if not event or not event.is_active:
            raise NotFoundError("Event not found")
        previous = event.poster_url
        event.poster_url = new_poster_url
        await db.commit()
        loaded = await CatalogManager.get_event_by_id(event_id, db, include_inactive=True)
        if loaded is None:
            raise NotFoundError("Event not found")
        return loaded, previous

    @staticmethod
    async def soft_delete_event(event_id: uuid.UUID, db):
        result = await db.execute(select(Event).where(Event.id == event_id))
        event = result.scalar_one_or_none()
        if not event:
            raise NotFoundError("Event not found")
        if not event.is_active:
            return

        event.is_active = False
        sessions_result = await db.execute(select(Session).where(Session.event_id == event.id, Session.is_active == True))  # noqa: E712
        sessions = sessions_result.scalars().all()
        for session in sessions:
            session.is_active = False
        await db.commit()

    @staticmethod
    async def create_category(data: CategoryCreate, db):
        duplicate = await db.execute(
            select(Category).where(
                or_(
                    Category.name_ru == data.name_ru,
                    Category.name_en == data.name_en,
                    Category.name_kz == data.name_kz,
                )
            )
        )
        if duplicate.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Category with one of these names already exists")

        new_category = Category(name_ru=data.name_ru, name_en=data.name_en, name_kz=data.name_kz)
        db.add(new_category)
        await db.commit()
        await db.refresh(new_category)
        return new_category

    @staticmethod
    async def update_category(category_id: uuid.UUID, data: CategoryUpdate, db):
        result = await db.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        if not category:
            raise NotFoundError("Category not found")

        if data.name_ru is not None:
            category.name_ru = data.name_ru
        if data.name_en is not None:
            category.name_en = data.name_en
        if data.name_kz is not None:
            category.name_kz = data.name_kz

        await db.commit()
        await db.refresh(category)
        return category

    @staticmethod
    async def delete_category(category_id: uuid.UUID, db):
        result = await db.execute(select(Category).where(Category.id == category_id))
        category = result.scalar_one_or_none()
        if not category:
            raise NotFoundError("Category not found")

        category.is_active = False
        await db.commit()

    @staticmethod
    async def get_all_categories(db):
        result = await db.execute(
            select(Category).where(Category.is_active == True).order_by(Category.name_ru)  # noqa: E712
        )
        return result.scalars().all()

    @staticmethod
    async def create_city(data: CityCreate, db):
        duplicate = await db.execute(
            select(City).where(
                or_(
                    City.name_ru == data.name_ru,
                    City.name_en == data.name_en,
                    City.name_kz == data.name_kz,
                )
            )
        )
        if duplicate.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="City with one of these names already exists")

        new_city = City(name_ru=data.name_ru, name_en=data.name_en, name_kz=data.name_kz)
        db.add(new_city)
        await db.commit()
        await db.refresh(new_city)
        return new_city

    @staticmethod
    async def update_city(city_id: uuid.UUID, data: CityUpdate, db):
        result = await db.execute(select(City).where(City.id == city_id))
        city = result.scalar_one_or_none()
        if not city:
            raise NotFoundError("City not found")

        if data.name_ru is not None:
            city.name_ru = data.name_ru
        if data.name_en is not None:
            city.name_en = data.name_en
        if data.name_kz is not None:
            city.name_kz = data.name_kz

        await db.commit()
        await db.refresh(city)
        return city

    @staticmethod
    async def delete_city(city_id: uuid.UUID, db):
        result = await db.execute(select(City).where(City.id == city_id))
        city = result.scalar_one_or_none()
        if not city:
            raise NotFoundError("City not found")

        city.is_active = False
        await db.commit()

    @staticmethod
    async def get_all_cities(db):
        result = await db.execute(
            select(City).where(City.is_active == True).order_by(City.name_ru)  # noqa: E712
        )
        return result.scalars().all()

    @staticmethod
    async def get_session_by_id(session_id: uuid.UUID, db, include_inactive: bool = False):
        stmt = select(Session).where(Session.id == session_id)
        if not include_inactive:
            stmt = stmt.where(Session.is_active == True)  # noqa: E712
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_session(session_id: uuid.UUID, data: SessionUpdate, db):
        result = await db.execute(select(Session).where(Session.id == session_id))
        session_obj = result.scalar_one_or_none()
        if not session_obj or not session_obj.is_active:
            raise NotFoundError("Session not found")

        if data.start_time is not None:
            session_obj.start_time = data.start_time
        if data.hall_name is not None:
            session_obj.hall_name = data.hall_name
        if data.price is not None:
            await _sync_seat_prices_for_session(session_id, data.price)
            session_obj.price = data.price

        await db.commit()
        await db.refresh(session_obj)
        return session_obj

    @staticmethod
    async def soft_delete_session(session_id: uuid.UUID, db):
        result = await db.execute(select(Session).where(Session.id == session_id))
        session_obj = result.scalar_one_or_none()
        if not session_obj:
            raise NotFoundError("Session not found")
        if not session_obj.is_active:
            return
        session_obj.is_active = False
        await db.commit()
