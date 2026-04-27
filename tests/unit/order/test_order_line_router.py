"""Tests for the OrderLine router CRUD endpoints — closes the
83% coverage gap on `order_line_router.py` (lines 51-53 list,
67 / 71-74 add error paths, 167-175 delete).

Sibling spec to `test_order_line_status_update.py` which already
covers the PATCH /status endpoint shipped via !47.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _seed_customer_and_product(client: AsyncClient) -> tuple[int, int]:
    customer = await client.post(
        "/customers",
        json={"name": "Line-Buyer", "email": "line-buyer@example.com"},
    )
    customer_id = customer.json()["id"]
    product = await client.post(
        "/products",
        json={
            "name": "Line-Widget",
            "description": "test",
            "unit_price": "9.99",
            "stock_quantity": 100,
        },
    )
    product_id = product.json()["id"]
    return customer_id, product_id


# ── GET /orders/{order_id}/lines ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_lines_empty_order_returns_empty_array(client: AsyncClient) -> None:
    """An order without lines returns 200 + []."""
    customer_id, _ = await _seed_customer_and_product(client)
    order = await client.post("/orders", json={"customer_id": customer_id})
    order_id = order.json()["id"]

    response = await client.get(f"/orders/{order_id}/lines")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_lines_returns_lines_in_id_order(client: AsyncClient) -> None:
    """Lines come back ordered by id ASC (matches Java parity)."""
    customer_id, product_id = await _seed_customer_and_product(client)
    order = await client.post("/orders", json={"customer_id": customer_id})
    order_id = order.json()["id"]

    line1 = await client.post(
        f"/orders/{order_id}/lines",
        json={"product_id": product_id, "quantity": 1},
    )
    line2 = await client.post(
        f"/orders/{order_id}/lines",
        json={"product_id": product_id, "quantity": 3},
    )

    response = await client.get(f"/orders/{order_id}/lines")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["id"] == line1.json()["id"]
    assert body[1]["id"] == line2.json()["id"]
    assert body[0]["quantity"] == 1
    assert body[1]["quantity"] == 3


# ── POST /orders/{order_id}/lines (error paths) ──────────────────────────────


@pytest.mark.asyncio
async def test_add_line_unknown_order_returns_404(client: AsyncClient) -> None:
    """Adding a line to a non-existent order → 404."""
    _, product_id = await _seed_customer_and_product(client)

    response = await client.post(
        "/orders/99999/lines",
        json={"product_id": product_id, "quantity": 1},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_add_line_unknown_product_returns_422(client: AsyncClient) -> None:
    """Adding a line referencing a non-existent product → 422 (FK
    violation surfaced as Unprocessable Entity rather than 500)."""
    customer_id, _ = await _seed_customer_and_product(client)
    order = await client.post("/orders", json={"customer_id": customer_id})
    order_id = order.json()["id"]

    response = await client.post(
        f"/orders/{order_id}/lines",
        json={"product_id": 999999, "quantity": 1},
    )

    assert response.status_code == 422
    assert "999999" in response.json()["detail"]


# ── DELETE /orders/{order_id}/lines/{line_id} ────────────────────────────────


@pytest.mark.asyncio
async def test_delete_line_recomputes_order_total(client: AsyncClient) -> None:
    """DELETE on a line removes it AND triggers Order.total_amount
    recomputation. Two lines x 9.99 = 19.98 ; after deleting one, the
    order total should be 9.99."""
    customer_id, product_id = await _seed_customer_and_product(client)
    order = await client.post("/orders", json={"customer_id": customer_id})
    order_id = order.json()["id"]

    line1 = await client.post(
        f"/orders/{order_id}/lines",
        json={"product_id": product_id, "quantity": 1},
    )
    await client.post(
        f"/orders/{order_id}/lines",
        json={"product_id": product_id, "quantity": 1},
    )
    # Initial total = 2 x 9.99 = 19.98
    initial = (await client.get(f"/orders/{order_id}")).json()["total_amount"]
    assert initial == "19.98"

    delete = await client.delete(f"/orders/{order_id}/lines/{line1.json()['id']}")
    assert delete.status_code == 204

    final = (await client.get(f"/orders/{order_id}")).json()["total_amount"]
    assert final == "9.99"


@pytest.mark.asyncio
async def test_delete_line_unknown_id_returns_404(client: AsyncClient) -> None:
    """DELETE on a non-existent line id → 404."""
    customer_id, _ = await _seed_customer_and_product(client)
    order = await client.post("/orders", json={"customer_id": customer_id})
    order_id = order.json()["id"]

    response = await client.delete(f"/orders/{order_id}/lines/999999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_line_url_spoofing_returns_404(client: AsyncClient) -> None:
    """Line exists but URL's order_id mismatch — 404 to avoid leaking
    line existence (same pattern as the PATCH /status endpoint)."""
    customer_id, product_id = await _seed_customer_and_product(client)
    order_a = await client.post("/orders", json={"customer_id": customer_id})
    order_a_id = order_a.json()["id"]
    line = await client.post(
        f"/orders/{order_a_id}/lines",
        json={"product_id": product_id, "quantity": 1},
    )
    line_id = line.json()["id"]

    # Try to delete via a DIFFERENT order's URL.
    spoofed_order_id = order_a_id + 999
    response = await client.delete(f"/orders/{spoofed_order_id}/lines/{line_id}")

    assert response.status_code == 404
    # The line must still exist after the spoofed delete attempt.
    refreshed = (await client.get(f"/orders/{order_a_id}/lines")).json()
    assert len(refreshed) == 1
    assert refreshed[0]["id"] == line_id
