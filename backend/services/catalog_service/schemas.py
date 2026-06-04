import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name_ru: str
    name_en: str
    name_kz: str
    model_config = ConfigDict(from_attributes=True)


class CityResponse(BaseModel):
    id: uuid.UUID
    name_ru: str
    name_en: str
    name_kz: str
    model_config = ConfigDict(from_attributes=True)


class SessionResponse(BaseModel):
    id: uuid.UUID
    start_time: datetime
    hall_name: str
    price: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    poster_url: Optional[str] = None
    video_url: Optional[str] = Field(default=None, max_length=1000)
    category_id: uuid.UUID
    city_id: uuid.UUID


class EventResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    poster_url: Optional[str] = None
    video_url: Optional[str] = None
    is_active: bool

    category: CategoryResponse
    city: CityResponse
    sessions: List[SessionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class EventListResponse(BaseModel):
    """Список мероприятий с метаданными пагинации (как в админских списках)."""

    events: List[EventResponse]
    total: int
    page: int
    limit: int
    totalPages: int


class SessionCreate(BaseModel):
    start_time: datetime
    hall_name: str
    price: int


class SessionUpdate(BaseModel):
    start_time: Optional[datetime] = None
    hall_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    price: Optional[int] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def require_at_least_one(self) -> "SessionUpdate":
        if self.start_time is None and self.hall_name is None and self.price is None:
            raise ValueError("At least one of start_time, hall_name, or price must be provided")
        return self

    model_config = ConfigDict(extra="forbid")


class CategoryCreate(BaseModel):
    name_ru: str
    name_en: str
    name_kz: str


class CategoryUpdate(BaseModel):
    name_ru: Optional[str] = None
    name_en: Optional[str] = None
    name_kz: Optional[str] = None


class CityCreate(BaseModel):
    name_ru: str
    name_en: str
    name_kz: str


class CityUpdate(BaseModel):
    name_ru: Optional[str] = None
    name_en: Optional[str] = None
    name_kz: Optional[str] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    poster_url: Optional[str] = None
    video_url: Optional[str] = Field(default=None, max_length=1000)
    category_id: Optional[uuid.UUID] = None
    city_id: Optional[uuid.UUID] = None
