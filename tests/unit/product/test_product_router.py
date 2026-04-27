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
async def test_update_returns_200_with_new_fields(client: AsyncClient) -> None:
    """PUT /products/{id} replaces fields and returns 200 with updated DTO."""
    created = await client.post(
        "/products",
        json={"name": "Original", "unit_price": "10.00", "stock_quantity": 5},
    )
    pid = created.json()["id"]

    response = await client.put(
        f"/products/{pid}",
        json={
            "name": "Updated",
            "description": "now with desc",
            "unit_price": "20.00",
            "stock_quantity": 10,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == pid
    assert body["name"] == "Updated"
    assert body["description"] == "now with desc"
    assert body["unit_price"] == "20.00"
    assert body["stock_quantity"] == 10


@pytest.mark.asyncio
async def test_update_404_when_missing(client: AsyncClient) -> None:
    """PUT on non-existent id returns 404 (no implicit upsert — matches Java)."""
    response = await client.put(
        "/products/99999",
        json={"name": "Ghost", "unit_price": "1.00", "stock_quantity": 0},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_validates_negative_stock(client: AsyncClient) -> None:
    """PUT with negative stock returns 422 from Pydantic validation."""
    created = await client.post(
        "/products",
        json={"name": "Existing", "unit_price": "5.00", "stock_quantity": 1},
    )
    pid = created.json()["id"]
    response = await client.put(
        f"/products/{pid}",
        json={"name": "X", "unit_price": "5.00", "stock_quantity": -1},
    )
    assert response.status_code == 422


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


# ── /products?search= ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_filters_by_name_substring(client: AsyncClient) -> None:
    """search="lap" matches "Laptop" + "Lapdog" (case-insensitive substring)."""
    for name, desc in (
        ("Laptop Stand", "ergonomic"),
        ("Lapdog Carrier", "small dog"),
        ("Mouse", "wireless"),
    ):
        await client.post(
            "/products",
            json={"name": name, "description": desc, "unit_price": "9.99", "stock_quantity": 1},
        )

    response = await client.get("/products?search=lap")
    assert response.status_code == 200
    body = response.json()
    names = [p["name"] for p in body["items"]]
    assert names == ["Laptop Stand", "Lapdog Carrier"]
    assert body["total"] == 2


@pytest.mark.asyncio
async def test_search_filters_by_description(client: AsyncClient) -> None:
    """search="ergonomic" matches the Laptop Stand by description, NOT the rest."""
    for name, desc in (
        ("Laptop Stand", "ergonomic"),
        ("Mouse", "wireless"),
    ):
        await client.post(
            "/products",
            json={"name": name, "description": desc, "unit_price": "9.99", "stock_quantity": 1},
        )

    response = await client.get("/products?search=ergonomic")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "Laptop Stand"


@pytest.mark.asyncio
async def test_search_is_case_insensitive(client: AsyncClient) -> None:
    """search="LAPTOP" matches "Laptop Stand" (the lower() normalisation)."""
    await client.post(
        "/products",
        json={"name": "Laptop Stand", "unit_price": "9.99", "stock_quantity": 1},
    )

    response = await client.get("/products?search=LAPTOP")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_search_empty_string_returns_unfiltered(client: AsyncClient) -> None:
    """search="" must NOT degrade to LIKE '%%' — falls through to list_paginated."""
    for i in range(3):
        await client.post(
            "/products",
            json={"name": f"P{i}", "unit_price": "1.00", "stock_quantity": 1},
        )

    response = await client.get("/products?search=")
    assert response.status_code == 200
    assert response.json()["total"] == 3


@pytest.mark.asyncio
async def test_search_whitespace_only_returns_unfiltered(client: AsyncClient) -> None:
    """search="   " trimmed to empty → unfiltered list."""
    for i in range(3):
        await client.post(
            "/products",
            json={"name": f"P{i}", "unit_price": "1.00", "stock_quantity": 1},
        )

    response = await client.get("/products?search=%20%20%20")
    assert response.status_code == 200
    assert response.json()["total"] == 3


@pytest.mark.asyncio
async def test_search_no_match_returns_empty_page(client: AsyncClient) -> None:
    """search="xyz" with nothing matching → 200 + empty items + total=0."""
    await client.post(
        "/products",
        json={"name": "Laptop", "unit_price": "9.99", "stock_quantity": 1},
    )

    response = await client.get("/products?search=xyz")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0
