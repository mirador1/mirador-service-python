"""Product router CRUD tests — async + httpx + in-memory SQLite.

Mirrors Java's `ProductControllerTest` shape : list / get / create /
delete + happy paths + 404 + 409.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_empty(client: AsyncClient) -> None:
    """Empty product list returns 200 with empty items + total=0."""
    response = await client.get("/products")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["page"] == 0
    assert body["size"] == 20


@pytest.mark.asyncio
async def test_create_returns_201(client: AsyncClient) -> None:
    """POST /products returns 201 + the created product with id assigned."""
    response = await client.post(
        "/products",
        json={
            "name": "Widget",
            "description": "A useful widget",
            "unit_price": "9.99",
            "stock_quantity": 100,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Widget"
    assert body["description"] == "A useful widget"
    assert body["unit_price"] == "9.99"
    assert body["stock_quantity"] == 100
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body


@pytest.mark.asyncio
async def test_create_then_get_by_id(client: AsyncClient) -> None:
    """Created product is retrievable by its id."""
    created = await client.post(
        "/products",
        json={"name": "Gadget", "unit_price": "19.99", "stock_quantity": 5},
    )
    pid = created.json()["id"]

    fetched = await client.get(f"/products/{pid}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Gadget"


@pytest.mark.asyncio
async def test_get_404_when_missing(client: AsyncClient) -> None:
    """GET on non-existent id returns 404."""
    response = await client.get("/products/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_with_minimal_fields(client: AsyncClient) -> None:
    """Creating a product without a description is OK (description nullable)."""
    response = await client.post(
        "/products",
        json={"name": "Minimal", "unit_price": "0.01", "stock_quantity": 0},
    )
    assert response.status_code == 201
    assert response.json()["description"] is None
    assert response.json()["stock_quantity"] == 0


@pytest.mark.asyncio
async def test_create_duplicate_name_returns_409(client: AsyncClient) -> None:
    """A second product with the same name returns 409 Conflict."""
    payload = {"name": "Unique", "unit_price": "1.00", "stock_quantity": 1}
    first = await client.post("/products", json=payload)
    assert first.status_code == 201

    second = await client.post("/products", json=payload)
    assert second.status_code == 409
    assert "already exists" in second.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_negative_price_returns_422(client: AsyncClient) -> None:
    """Negative unit_price rejected by Pydantic validation (422)."""
    response = await client.post(
        "/products",
        json={"name": "BadPrice", "unit_price": "-1.00", "stock_quantity": 0},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_negative_stock_returns_422(client: AsyncClient) -> None:
    """Negative stock_quantity rejected by Pydantic validation (422)."""
    response = await client.post(
        "/products",
        json={"name": "BadStock", "unit_price": "1.00", "stock_quantity": -5},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_blank_name_returns_422(client: AsyncClient) -> None:
    """Empty name rejected by Pydantic min_length=1."""
    response = await client.post(
        "/products",
        json={"name": "", "unit_price": "1.00", "stock_quantity": 1},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_returns_204(client: AsyncClient) -> None:
    """DELETE returns 204 No Content + product becomes 404 afterwards."""
    created = await client.post(
        "/products",
        json={"name": "ToDelete", "unit_price": "5.00", "stock_quantity": 1},
    )
    pid = created.json()["id"]

    delete_resp = await client.delete(f"/products/{pid}")
    assert delete_resp.status_code == 204

    after = await client.get(f"/products/{pid}")
    assert after.status_code == 404


@pytest.mark.asyncio
async def test_delete_404_when_missing(client: AsyncClient) -> None:
    """DELETE on non-existent id returns 404 (not idempotent — match Java)."""
    response = await client.delete("/products/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_pagination(client: AsyncClient) -> None:
    """Create 5 products, request page 0 size 2, expect 2 items + total=5."""
    for i in range(5):
        await client.post(
            "/products",
            json={
                "name": f"P{i}",
                "unit_price": f"{i}.00",
                "stock_quantity": i,
            },
        )

    response = await client.get("/products?page=0&size=2")
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] == 5
    assert body["page"] == 0
    assert body["size"] == 2
