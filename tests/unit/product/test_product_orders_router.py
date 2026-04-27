"""Tests for ``GET /products/{product_id}/orders`` — the server-side
"orders containing this product" endpoint that replaces the UI's
client-side fan-out.

Mirrors Java's ``ProductControllerTest#ordersForProduct_*``. Uses the
shared in-memory SQLite + ASGI fixture from ``conftest.py`` so the
tests exercise the real router + repository + ORM stack — only the
DB engine is swapped out.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _create_product(client: AsyncClient, name: str, *, unit_price: str = "9.99", stock: int = 5) -> int:
    """Helper — POST /products and return the new id."""
    response = await client.post(
        "/products",
        json={"name": name, "unit_price": unit_price, "stock_quantity": stock},
    )
    assert response.status_code == 201
    return int(response.json()["id"])


async def _create_customer(client: AsyncClient, name: str) -> int:
    """Helper — POST /customers and return the new id.

    Order has FK to customer ; the test stack creates the customer table
    on connect (via ``Base.metadata.create_all``) so a real customer row
    is the cheapest way to satisfy the FK.
    """
    response = await client.post(
        "/customers",
        json={"name": name, "email": f"{name.lower()}@example.com"},
    )
    assert response.status_code == 201
    return int(response.json()["id"])


async def _create_order_with_line(
    client: AsyncClient,
    customer_id: int,
    product_id: int,
    *,
    quantity: int = 1,
) -> int:
    """Helper — POST /orders + POST /orders/{id}/lines, return order id."""
    order = await client.post("/orders", json={"customer_id": customer_id})
    assert order.status_code == 201
    order_id = int(order.json()["id"])
    line = await client.post(
        f"/orders/{order_id}/lines",
        json={"product_id": product_id, "quantity": quantity},
    )
    assert line.status_code == 201
    return order_id


@pytest.mark.asyncio
async def test_orders_for_product_returns_404_when_product_missing(client: AsyncClient) -> None:
    """Path-level 404 — typoed product id MUST NOT silently return empty.

    The UI consumer needs to distinguish "no orders yet" (legitimate
    empty page on an existing product) from "wrong product id" (path
    error). A 404 here is the explicit signal.
    """
    response = await client.get("/products/99999/orders")
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


@pytest.mark.asyncio
async def test_orders_for_product_returns_empty_page_for_existing_unsold_product(
    client: AsyncClient,
) -> None:
    """An existing product with zero orders returns 200 + empty items + total=0.

    Distinct from the missing-product 404 case — that contract lets the
    UI badge "no orders yet" without ambiguity.
    """
    pid = await _create_product(client, "UnsoldGadget")

    response = await client.get(f"/products/{pid}/orders")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["page"] == 0
    assert body["size"] == 20


@pytest.mark.asyncio
async def test_orders_for_product_returns_only_orders_containing_that_product(
    client: AsyncClient,
) -> None:
    """Server-side filter — only orders with a line for this product show up.

    Three orders are created : two contain the target product, one
    contains a different product. The endpoint MUST return exactly the
    two matching orders, not the third.
    """
    customer_id = await _create_customer(client, "Alice")
    target_pid = await _create_product(client, "Target")
    other_pid = await _create_product(client, "Other")

    matching_a = await _create_order_with_line(client, customer_id, target_pid)
    matching_b = await _create_order_with_line(client, customer_id, target_pid, quantity=3)
    await _create_order_with_line(client, customer_id, other_pid)

    response = await client.get(f"/products/{target_pid}/orders")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    returned_ids = {item["id"] for item in body["items"]}
    assert returned_ids == {matching_a, matching_b}


@pytest.mark.asyncio
async def test_orders_for_product_paginates(client: AsyncClient) -> None:
    """Pagination works on the filtered set — page 0 size 2 over 5 matching orders.

    Pinned : ``total`` reflects the FILTERED count (5), not the global
    order count. Size cap (le=100) is enforced by the route signature ;
    no separate test needed for that boundary because Pydantic produces
    a 422.
    """
    customer_id = await _create_customer(client, "Bob")
    target_pid = await _create_product(client, "Bestseller")
    for _ in range(5):
        await _create_order_with_line(client, customer_id, target_pid)

    response = await client.get(f"/products/{target_pid}/orders?page=0&size=2")
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] == 5
    assert body["page"] == 0
    assert body["size"] == 2
