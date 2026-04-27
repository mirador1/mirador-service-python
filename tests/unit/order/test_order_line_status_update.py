"""Tests for PATCH /orders/{order_id}/lines/{line_id}/status (ADR-0063).

Mirrors Java's `OrderLineControllerStatusTest`. Covers the 5 paths an
HTTP client can drive : valid forward, 404 missing line, 404 spoofed
order_id mismatch, 409 forbidden transition (skip PENDING → REFUNDED),
self-transition idempotency.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _seed_order_with_line(client: AsyncClient) -> tuple[int, int, int]:
    """Helper : create customer + product + order + 1 line. Returns
    (customer_id, order_id, line_id). Each test starts from a fresh
    PENDING line so the state machine has a clean source."""
    customer = await client.post(
        "/customers",
        json={"name": "Refund-Buyer", "email": "refund@example.com"},
    )
    customer_id = customer.json()["id"]

    product = await client.post(
        "/products",
        json={
            "name": "Refund-Widget",
            "description": "test",
            "unit_price": "9.99",
            "stock_quantity": 100,
        },
    )
    product_id = product.json()["id"]

    order = await client.post("/orders", json={"customer_id": customer_id})
    order_id = order.json()["id"]

    line = await client.post(
        f"/orders/{order_id}/lines",
        json={"product_id": product_id, "quantity": 2},
    )
    line_id = line.json()["id"]
    return customer_id, order_id, line_id


@pytest.mark.asyncio
async def test_update_line_status_valid_forward_transition(client: AsyncClient) -> None:
    """PENDING → SHIPPED is allowed by the state machine."""
    _, order_id, line_id = await _seed_order_with_line(client)

    response = await client.patch(
        f"/orders/{order_id}/lines/{line_id}/status",
        json={"status": "SHIPPED"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "SHIPPED"


@pytest.mark.asyncio
async def test_update_line_status_unknown_line_returns_404(client: AsyncClient) -> None:
    response = await client.patch(
        "/orders/1/lines/999999/status",
        json={"status": "SHIPPED"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_line_status_url_spoofing_returns_404(client: AsyncClient) -> None:
    """Line exists but URL's order_id doesn't match — must 404 (don't
    leak existence by 400ing on the order mismatch)."""
    _, order_id, line_id = await _seed_order_with_line(client)
    spoofed = order_id + 999

    response = await client.patch(
        f"/orders/{spoofed}/lines/{line_id}/status",
        json={"status": "SHIPPED"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_line_status_skip_pending_to_refunded_returns_409(client: AsyncClient) -> None:
    """PENDING → REFUNDED skips the SHIPPED gate ; rejected per
    ADR-0063 §'Decision' (audit traceability)."""
    _, order_id, line_id = await _seed_order_with_line(client)

    response = await client.patch(
        f"/orders/{order_id}/lines/{line_id}/status",
        json={"status": "REFUNDED", "reason": "customer disputed charge"},
    )

    assert response.status_code == 409
    body = response.json()["detail"]
    assert body["currentStatus"] == "PENDING"
    assert body["targetStatus"] == "REFUNDED"
    assert body["reason"] == "customer disputed charge"


@pytest.mark.asyncio
async def test_update_line_status_self_transition_idempotent(client: AsyncClient) -> None:
    """PENDING → PENDING is allowed (retry safe)."""
    _, order_id, line_id = await _seed_order_with_line(client)

    response = await client.patch(
        f"/orders/{order_id}/lines/{line_id}/status",
        json={"status": "PENDING"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "PENDING"


@pytest.mark.asyncio
async def test_update_line_status_unknown_value_returns_422(client: AsyncClient) -> None:
    """Pydantic Literal rejects unknown statuses at the boundary."""
    _, order_id, line_id = await _seed_order_with_line(client)

    response = await client.patch(
        f"/orders/{order_id}/lines/{line_id}/status",
        json={"status": "DELIVERED"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_line_status_full_path_pending_shipped_refunded(client: AsyncClient) -> None:
    """End-to-end : PENDING → SHIPPED → REFUNDED, all 200 + final
    status REFUNDED (state machine accepts the full forward chain)."""
    _, order_id, line_id = await _seed_order_with_line(client)

    r1 = await client.patch(
        f"/orders/{order_id}/lines/{line_id}/status",
        json={"status": "SHIPPED", "reason": "carrier picked up"},
    )
    assert r1.status_code == 200
    assert r1.json()["status"] == "SHIPPED"

    r2 = await client.patch(
        f"/orders/{order_id}/lines/{line_id}/status",
        json={"status": "REFUNDED", "reason": "customer-service goodwill"},
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "REFUNDED"


@pytest.mark.asyncio
async def test_update_line_status_does_not_change_order_total(client: AsyncClient) -> None:
    """Refund does NOT mutate the snapshot price — Order.total_amount
    stays unchanged per ADR-0063 §'Refund refunds the snapshot'."""
    _, order_id, line_id = await _seed_order_with_line(client)

    initial_total = (await client.get(f"/orders/{order_id}")).json()["total_amount"]

    # Walk to SHIPPED then REFUNDED.
    await client.patch(
        f"/orders/{order_id}/lines/{line_id}/status",
        json={"status": "SHIPPED"},
    )
    await client.patch(
        f"/orders/{order_id}/lines/{line_id}/status",
        json={"status": "REFUNDED"},
    )

    final_total = (await client.get(f"/orders/{order_id}")).json()["total_amount"]
    assert initial_total == final_total
