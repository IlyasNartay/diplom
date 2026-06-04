import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from services.catalog_service.database import get_db
from services.catalog_service.logic.catalog_manager import CatalogManager
from services.catalog_service.logic.poster_storage import delete_owned_poster_file, save_event_poster
from services.catalog_service.schemas import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CityCreate,
    CityUpdate,
    CityResponse,
    EventCreate,
    EventListResponse,
    EventUpdate,
    EventResponse,
    SessionCreate,
    SessionUpdate,
    SessionResponse,
)

router = APIRouter()


@router.get(
    "/events",
    response_model=EventListResponse,
    tags=["Events"],
    summary="Список мероприятий с пагинацией",
    description="Query: page (с 1), limit (1–1000). Без limit возвращаются все записи; в теле тогда limit=total, page=1, totalPages=1. Заголовок X-Total-Count = total.",
)
async def list_events(
    response: Response,
    category_id: Optional[uuid.UUID] = Query(default=None),
    city_id: Optional[uuid.UUID] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: Optional[int] = Query(default=None, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    sql_offset = (page - 1) * limit if limit is not None else None

    items, total = await CatalogManager.list_events(
        db=db,
        category_id=category_id,
        city_id=city_id,
        limit=limit,
        offset=sql_offset,
    )
    response.headers["X-Total-Count"] = str(total)

    if limit is None:
        meta_limit = total
        meta_page = 1
        total_pages = 1
    else:
        meta_limit = limit
        meta_page = page
        total_pages = max(1, (total + limit - 1) // limit) if total > 0 else 1

    return EventListResponse(
        events=items,
        total=total,
        page=meta_page,
        limit=meta_limit,
        totalPages=total_pages,
    )


@router.get("/sessions", response_model=List[SessionResponse], tags=["Sessions"], summary="Список всех активных сеансов")
async def list_sessions(db: AsyncSession = Depends(get_db)):
    return await CatalogManager.get_all_sessions(db)


@router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    tags=["Sessions"],
    summary="Детали сеанса",
)
async def get_session(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    session_obj = await CatalogManager.get_session_by_id(session_id, db)
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_obj


@router.get(
    "/events/{event_id}", response_model=EventResponse, tags=["Events"], summary="Детали конкретного мероприятия"
)
async def get_event(event_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    event = await CatalogManager.get_event_by_id(event_id, db)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.get(
    "/events/{event_id}/sessions",
    response_model=List[SessionResponse],
    tags=["Sessions"],
    summary="Список активных сеансов мероприятия",
)
async def list_event_sessions(event_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    event = await CatalogManager.get_event_by_id(event_id, db)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return await CatalogManager.get_sessions_by_event_id(event_id, db)


@router.post("/admin/events", response_model=EventResponse, tags=["Admin"], summary="Создать новое мероприятие")
async def create_event(data: EventCreate, db: AsyncSession = Depends(get_db)):
    return await CatalogManager.create_event(data, db)


@router.post(
    "/admin/events/form",
    response_model=EventResponse,
    tags=["Admin"],
    summary="Создать мероприятие (multipart/form-data)",
    description="Поля формы: title, category_id, city_id; опционально description, video_url (трейлер YouTube и т.д.), файл poster.",
)
async def create_event_form(
    title: str = Form(...),
    category_id: uuid.UUID = Form(...),
    city_id: uuid.UUID = Form(...),
    description: Optional[str] = Form(None),
    video_url: Optional[str] = Form(None),
    poster: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
):
    poster_url = None
    if poster is not None and (poster.filename or "").strip():
        poster_url = await save_event_poster(poster)
    payload = EventCreate(
        title=title,
        description=description,
        poster_url=poster_url,
        video_url=(video_url or None),
        category_id=category_id,
        city_id=city_id,
    )
    return await CatalogManager.create_event(payload, db)


@router.put("/admin/events/{event_id}", response_model=EventResponse, tags=["Admin"], summary="Обновить мероприятие")
async def update_event(event_id: uuid.UUID, data: EventUpdate, db: AsyncSession = Depends(get_db)):
    return await CatalogManager.update_event(event_id, data, db)


@router.post(
    "/admin/events/{event_id}/poster",
    response_model=EventResponse,
    tags=["Admin"],
    summary="Загрузить или заменить постер мероприятия",
    description="multipart/form-data: поле poster — файл изображения (JPEG, PNG, WebP). Старый файл из каталога posters удаляется, если он был загружен через этот сервис.",
)
async def upload_event_poster(
    event_id: uuid.UUID,
    poster: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    new_url = await save_event_poster(poster)
    event, previous_url = await CatalogManager.replace_event_poster_url(event_id, new_url, db)
    delete_owned_poster_file(previous_url)
    return event


@router.delete("/admin/events/{event_id}", tags=["Admin"], summary="Скрыть мероприятие (soft delete)")
async def delete_event(event_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await CatalogManager.soft_delete_event(event_id, db)
    return {"detail": "Event deleted successfully"}


@router.post(
    "/admin/events/{event_id}/sessions",
    response_model=SessionResponse,
    tags=["Admin"],
    summary="Добавить сеанс к мероприятию",
)
async def create_session(event_id: uuid.UUID, data: SessionCreate, db: AsyncSession = Depends(get_db)):
    event = await CatalogManager.get_event_by_id(event_id, db, include_inactive=True)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return await CatalogManager.create_session(event_id, data, db)


@router.put(
    "/admin/sessions/{session_id}",
    response_model=SessionResponse,
    tags=["Admin"],
    summary="Обновить сеанс (зал и/или цену)",
    description="Можно передать hall_name и/или price. При смене price все места этого сеанса в seat_service получают ту же цену.",
)
async def update_session(session_id: uuid.UUID, data: SessionUpdate, db: AsyncSession = Depends(get_db)):
    return await CatalogManager.update_session(session_id, data, db)


@router.delete("/admin/sessions/{session_id}", tags=["Admin"], summary="Скрыть сеанс (soft delete)")
async def delete_session(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await CatalogManager.soft_delete_session(session_id, db)
    return {"detail": "Session deleted successfully"}


@router.get("/cities", response_model=List[CityResponse], tags=["Cities"], summary="Список городов")
async def list_cities(db: AsyncSession = Depends(get_db)):
    return await CatalogManager.get_all_cities(db)


@router.post("/admin/cities", response_model=CityResponse, tags=["Cities"], summary="Добавить новый город")
async def create_city(data: CityCreate, db: AsyncSession = Depends(get_db)):
    return await CatalogManager.create_city(data, db)


@router.get("/categories", response_model=List[CategoryResponse], tags=["Categories"], summary="Список категорий")
async def list_categories(db: AsyncSession = Depends(get_db)):
    return await CatalogManager.get_all_categories(db)


@router.post(
    "/admin/categories", response_model=CategoryResponse, tags=["Categories"], summary="Добавить новую категорию"
)
async def create_category(data: CategoryCreate, db: AsyncSession = Depends(get_db)):
    return await CatalogManager.create_category(data, db)


@router.put(
    "/admin/categories/{category_id}",
    response_model=CategoryResponse,
    tags=["Categories"],
    summary="Обновить категорию",
)
async def update_category(category_id: uuid.UUID, data: CategoryUpdate, db: AsyncSession = Depends(get_db)):
    return await CatalogManager.update_category(category_id, data, db)


@router.delete(
    "/admin/categories/{category_id}",
    status_code=200,
    tags=["Categories"],
    summary="Скрыть категорию (soft delete)",
)
async def delete_category(category_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await CatalogManager.delete_category(category_id, db)
    return {"detail": "Category deleted successfully"}


@router.put(
    "/admin/cities/{city_id}",
    response_model=CityResponse,
    tags=["Cities"],
    summary="Обновить город",
)
async def update_city(city_id: uuid.UUID, data: CityUpdate, db: AsyncSession = Depends(get_db)):
    return await CatalogManager.update_city(city_id, data, db)


@router.delete(
    "/admin/cities/{city_id}",
    status_code=200,
    tags=["Cities"],
    summary="Скрыть город (soft delete)",
)
async def delete_city(city_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    await CatalogManager.delete_city(city_id, db)
    return {"detail": "City deleted successfully"}
