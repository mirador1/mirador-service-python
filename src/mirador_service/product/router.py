"""Product FastAPI router — mirrors Java's `ProductController`.

Foundation MR (2026-04-26) : list + get + create + delete. PUT (replace
+ partial) deferred to follow-up MR with optimistic locking + audit.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from mirador_service.db.base import get_db_session
from mirador_service.product.dtos import (
    ProductCreate,
    ProductPage,
    ProductResponse,
)
from mirador_service.product.models import Product
from mirador_service.product.repository import ProductRepository

router = APIRouter(prefix="/products", tags=["products"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("", response_model=ProductPage)
async def list_products(
    session: DbSession,
    page: Annotated[int, Query(ge=0)] = 0,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> ProductPage:
    """Paginated list of products."""
    repo = ProductRepository(session)
    items, total = await repo.list_paginated(page=page, size=size)
    return ProductPage(
        items=[ProductResponse.from_orm_entity(p) for p in items],
        total=total,
        page=page,
        size=size,
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, session: DbSession) -> ProductResponse:
    """Get product by ID — 404 if absent."""
    repo = ProductRepository(session)
    product = await repo.get_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return ProductResponse.from_orm_entity(product)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate, session: DbSession) -> ProductResponse:
    """Create a product. 409 if name already exists."""
    repo = ProductRepository(session)
    if await repo.find_by_name(payload.name) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product with name {payload.name!r} already exists",
        )
    product = Product(
        name=payload.name,
        description=payload.description,
        unit_price=payload.unit_price,
        stock_quantity=payload.stock_quantity,
    )
    try:
        saved = await repo.add(product)
    except IntegrityError as exc:
        # Race condition between find_by_name and add — DB unique constraint catches it.
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product name conflict (concurrent create)",
        ) from exc
    return ProductResponse.from_orm_entity(saved)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(product_id: int, payload: ProductCreate, session: DbSession) -> ProductResponse:
    """Update a product (replace fields). 404 if absent.

    Per shared ADR-0059, mutating `unit_price` here MUST NOT propagate to
    existing `OrderLine.unit_price_at_order` (snapshots are immutable).
    Repo only touches Product columns.
    """
    repo = ProductRepository(session)
    updated = await repo.update(
        product_id,
        name=payload.name,
        description=payload.description,
        unit_price=payload.unit_price,
        stock_quantity=payload.stock_quantity,
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return ProductResponse.from_orm_entity(updated)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, session: DbSession) -> None:
    """Delete a product. 404 if absent (idempotent variant skipped — match Java semantics)."""
    repo = ProductRepository(session)
    if not await repo.delete(product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
