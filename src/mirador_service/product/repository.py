"""Product async repository — SQLAlchemy 2.x async session pattern.

Mirrors Java's `ProductRepository` (Spring Data JpaRepository) but
made async since the whole Python service is async-first (cf. ADR-0008).
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mirador_service.product.models import Product


class ProductRepository:
    """Async DAO for `Product`. Stateless, takes the session per call."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_paginated(self, page: int, size: int) -> tuple[list[Product], int]:
        """Return (page_items, total_count) for the requested page.

        Page is 0-indexed (matches Java's Spring Data default). Size is
        clamped at the router level to avoid pathological queries.
        """
        offset = page * size
        items_stmt = select(Product).order_by(Product.id).offset(offset).limit(size)
        count_stmt = select(func.count()).select_from(Product)
        items = (await self.session.execute(items_stmt)).scalars().all()
        total = (await self.session.execute(count_stmt)).scalar_one()
        return list(items), total

    async def get_by_id(self, product_id: int) -> Product | None:
        return await self.session.get(Product, product_id)

    async def find_by_name(self, name: str) -> Product | None:
        """Cheap pre-create dup check — avoid catching IntegrityError."""
        stmt = select(Product).where(Product.name == name)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def add(self, product: Product) -> Product:
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def delete(self, product_id: int) -> bool:
        product = await self.session.get(Product, product_id)
        if product is None:
            return False
        await self.session.delete(product)
        await self.session.flush()
        return True
