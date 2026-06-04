import uuid
from typing import List

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from services.payment_service.database import get_db
from services.payment_service.logic.cards_manager import CardsManager
from services.payment_service.schemas import CardCreateRequest, CardResponse


router = APIRouter()


def _to_response(card) -> CardResponse:
    return CardResponse.model_validate(card)


@router.get(
    "/cards",
    response_model=List[CardResponse],
    summary="Список сохранённых карт текущего пользователя",
)
async def list_my_cards(
    x_user_id: uuid.UUID = Header(...),
    db: AsyncSession = Depends(get_db),
):
    cards = await CardsManager.list_cards(x_user_id, db)
    return [_to_response(c) for c in cards]


@router.post(
    "/cards",
    response_model=CardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Привязать новую карту",
    description=(
        "В теле: number, exp_month, exp_year, cvv, holder_name, is_default. "
        "В ответе номер маскируется до last4. Первая карта пользователя становится default автоматически."
    ),
)
async def add_card(
    body: CardCreateRequest,
    x_user_id: uuid.UUID = Header(...),
    db: AsyncSession = Depends(get_db),
):
    card = await CardsManager.add_card(x_user_id, body, db)
    return _to_response(card)


@router.patch(
    "/cards/{card_id}/default",
    response_model=CardResponse,
    summary="Сделать карту картой по умолчанию",
)
async def set_default_card(
    card_id: uuid.UUID,
    x_user_id: uuid.UUID = Header(...),
    db: AsyncSession = Depends(get_db),
):
    card = await CardsManager.set_default(x_user_id, card_id, db)
    return _to_response(card)


@router.delete(
    "/cards/{card_id}",
    status_code=status.HTTP_200_OK,
    summary="Удалить сохранённую карту",
)
async def delete_card(
    card_id: uuid.UUID,
    x_user_id: uuid.UUID = Header(...),
    db: AsyncSession = Depends(get_db),
):
    await CardsManager.delete_card(x_user_id, card_id, db)
    return {"detail": "Card deleted"}
