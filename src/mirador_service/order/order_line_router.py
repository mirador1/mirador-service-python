"""OrderLine FastAPI router — nested under /orders/{order_id}/lines.

Mirrors Java's OrderLineController. Snapshots Product.unit_price at
add-time + recomputes Order.total_amount in same transaction.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mirador_service.db.base import get_db_session
from mirador_service.order.models import Order
from mirador_service.order.order_line_models import OrderLine, OrderLineStatus
from mirador_service.product.models import Product

router = APIRouter(prefix="/orders/{order_id}/lines", tags=["order-lines"])

DbSession = Annotated[AsyncSession, Depends(get_db_session)]

OrderLineStatusLiteral = Literal["PENDING", "SHIPPED", "REFUNDED"]


class OrderLineCreate(BaseModel):
    """`POST /orders/{order_id}/lines` body. Price is snapshotted server-side."""

    product_id: Annotated[int, Field(gt=0)]
    quantity: Annotated[int, Field(gt=0)]


class OrderLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price_at_order: Decimal
    status: OrderLineStatusLiteral
    created_at: object  # datetime, kept loose for serialization


@router.get("", response_model=list[OrderLineResponse])
async def list_lines(order_id: int, session: DbSession) -> list[OrderLineResponse]:
    """List all lines of an order."""
    stmt = select(OrderLine).where(OrderLine.order_id == order_id).order_by(OrderLine.id)
    lines = (await session.execute(stmt)).scalars().all()
    return [OrderLineResponse.model_validate(l) for l in lines]


@router.post("", response_model=OrderLineResponse, status_code=status.HTTP_201_CREATED)
async def add_line(
    order_id: int,
    payload: OrderLineCreate,
    session: DbSession,
) -> OrderLineResponse:
    """Add a line to an order. Snapshots Product.unit_price + recomputes
    Order.total_amount in same transaction."""
    # Verify order exists
    order = await session.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    # Verify product exists + grab its current price for snapshot
    product = await session.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Product {payload.product_id} not found",
        )

    line = OrderLine(
        order_id=order_id,
        product_id=payload.product_id,
        quantity=payload.quantity,
        unit_price_at_order=product.unit_price,  # SNAPSHOT
        status=OrderLineStatus.PENDING.value,
    )
    session.add(line)
    await session.flush()
    await session.refresh(line)

    # Recompute Order.total_amount
    await _recompute_order_total(session, order)

    return OrderLineResponse.model_validate(line)


@router.delete("/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_line(order_id: int, line_id: int, session: DbSession) -> None:
    """Delete a line + recompute Order.total_amount."""
    line = await session.get(OrderLine, line_id)
    if line is None or line.order_id != order_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OrderLine not found")
    await session.delete(line)
    await session.flush()

    order = await session.get(Order, order_id)
    if order is not None:
        await _recompute_order_total(session, order)


async def _recompute_order_total(session: AsyncSession, order: Order) -> None:
    """Recompute order.total_amount = Σ(line.qty × line.unit_price_at_order)."""
    stmt = select(OrderLine).where(OrderLine.order_id == order.id)
    lines = (await session.execute(stmt)).scalars().all()
    total = sum((l.unit_price_at_order * l.quantity for l in lines), Decimal("0"))
    order.total_amount = total
    await session.flush()
