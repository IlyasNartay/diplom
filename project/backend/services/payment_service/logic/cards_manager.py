import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.errors import NotFoundError
from services.payment_service.models import SavedCard
from services.payment_service.schemas import CardCreateRequest, detect_brand


class CardsManager:
    @staticmethod
    async def list_cards(user_id: uuid.UUID, db: AsyncSession) -> list[SavedCard]:
        res = await db.execute(
            select(SavedCard)
            .where(SavedCard.user_id == user_id)
            .order_by(SavedCard.is_default.desc(), SavedCard.created_at.desc())
        )
        return list(res.scalars().all())

    @staticmethod
    async def get_card(user_id: uuid.UUID, card_id: uuid.UUID, db: AsyncSession) -> SavedCard:
        res = await db.execute(
            select(SavedCard).where(SavedCard.id == card_id, SavedCard.user_id == user_id)
        )
        card = res.scalar_one_or_none()
        if not card:
            raise NotFoundError("Card not found")
        return card

    @staticmethod
    async def add_card(user_id: uuid.UUID, data: CardCreateRequest, db: AsyncSession) -> SavedCard:
        existing = await CardsManager.list_cards(user_id, db)
        make_default = data.is_default or len(existing) == 0
        if make_default and existing:
            await db.execute(
                update(SavedCard).where(SavedCard.user_id == user_id).values(is_default=False)
            )

        card = SavedCard(
            user_id=user_id,
            brand=detect_brand(data.number),
            last4=data.number[-4:],
            pan_full=data.number,
            exp_month=data.exp_month,
            exp_year=data.exp_year,
            cvv=data.cvv,
            holder_name=data.holder_name,
            is_default=make_default,
        )
        db.add(card)
        await db.commit()
        await db.refresh(card)
        return card

    @staticmethod
    async def set_default(user_id: uuid.UUID, card_id: uuid.UUID, db: AsyncSession) -> SavedCard:
        card = await CardsManager.get_card(user_id, card_id, db)
        await db.execute(
            update(SavedCard).where(SavedCard.user_id == user_id).values(is_default=False)
        )
        card.is_default = True
        await db.commit()
        await db.refresh(card)
        return card

    @staticmethod
    async def delete_card(user_id: uuid.UUID, card_id: uuid.UUID, db: AsyncSession) -> None:
        card = await CardsManager.get_card(user_id, card_id, db)
        was_default = card.is_default
        await db.delete(card)
        await db.commit()
        if was_default:
            res = await db.execute(
                select(SavedCard).where(SavedCard.user_id == user_id).order_by(SavedCard.created_at.desc())
            )
            next_card = res.scalars().first()
            if next_card:
                next_card.is_default = True
                await db.commit()
