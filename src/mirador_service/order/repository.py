"""Order async repository — mirror of Java's OrderRepository."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mirador_service.order.models import Order


class OrderRepository:
    """Async DAO for `Order`."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_paginated(self, page: int, size: int) -> tuple[list[Order], int]:
        offset = page * size
        items_stmt = select(Order).order_by(Order.id.desc()).offset(offset).limit(size)
        count_stmt = select(func.count()).select_from(Order)
        items = (await self.session.execute(items_stmt)).scalars().all()
        total = (await self.session.execute(count_stmt)).scalar_one()
        return list(items), total

    async def get_by_id(self, order_id: int) -> Order | None:
        return await self.session.get(Order, order_id)

    async def add(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.flush()
        await self.session.refresh(order)
        return order

    async def delete(self, order_id: int) -> bool:
        order = await self.session.get(Order, order_id)
        if order is None:
            return False
        await self.session.delete(order)
        await self.session.flush()
        return True
