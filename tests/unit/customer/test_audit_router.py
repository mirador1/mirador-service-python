"""Audit endpoint tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_audit_returns_404_for_unknown_customer(client: AsyncClient) -> None:
    response = await client.get("/customers/999/audit")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_audit_returns_synthetic_trail(client: AsyncClient) -> None:
    create = await client.post("/customers", json={"name": "Audit", "email": "audit@example.com"})
    assert create.status_code == 201
    customer_id = create.json()["id"]

    response = await client.get(f"/customers/{customer_id}/audit")
    assert response.status_code == 200
    body = response.json()
    assert body["customerId"] == customer_id
    assert body["customerEmail"] == "audit@example.com"
    assert len(body["events"]) == 4
    assert body["events"][0]["event"] == "customer.created"
    assert body["events"][-1]["event"] == "customer.recent_buffer.added"
