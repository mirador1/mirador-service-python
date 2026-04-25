"""Customer router CRUD tests — async + httpx + in-memory SQLite."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_empty(client: AsyncClient) -> None:
    response = await client.get("/customers")
    assert response.status_code == 200
    body = response.json()
    assert body["content"] == []
    assert body["totalElements"] == 0
    # v1 deprecation header
    assert response.headers.get("Deprecation") == "true"


@pytest.mark.asyncio
async def test_create_returns_201(client: AsyncClient) -> None:
    response = await client.post(
        "/customers",
        json={"name": "Alice", "email": "alice@example.com"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Alice"
    assert body["email"] == "alice@example.com"
    assert "id" in body


@pytest.mark.asyncio
async def test_create_then_get_by_id(client: AsyncClient) -> None:
    created = await client.post(
        "/customers",
        json={"name": "Bob", "email": "bob@example.com"},
    )
    id_ = created.json()["id"]

    fetched = await client.get(f"/customers/{id_}")
    assert fetched.status_code == 200
    assert fetched.json()["email"] == "bob@example.com"


@pytest.mark.asyncio
async def test_get_404_when_missing(client: AsyncClient) -> None:
    response = await client.get("/customers/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_duplicate_email_returns_409(client: AsyncClient) -> None:
    await client.post("/customers", json={"name": "Alice", "email": "dup@example.com"})
    response = await client.post(
        "/customers",
        json={"name": "Alice2", "email": "dup@example.com"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_replaces_fields(client: AsyncClient) -> None:
    created = await client.post(
        "/customers",
        json={"name": "Old", "email": "old@example.com"},
    )
    id_ = created.json()["id"]

    response = await client.put(
        f"/customers/{id_}",
        json={"name": "New", "email": "new@example.com"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New"
    assert response.json()["email"] == "new@example.com"


@pytest.mark.asyncio
async def test_patch_partial_update(client: AsyncClient) -> None:
    created = await client.post(
        "/customers",
        json={"name": "Original", "email": "p@example.com"},
    )
    id_ = created.json()["id"]

    response = await client.patch(f"/customers/{id_}", json={"name": "Patched"})
    assert response.status_code == 200
    assert response.json()["name"] == "Patched"
    assert response.json()["email"] == "p@example.com"  # email unchanged


@pytest.mark.asyncio
async def test_delete_returns_204(client: AsyncClient) -> None:
    created = await client.post(
        "/customers",
        json={"name": "Delete", "email": "del@example.com"},
    )
    id_ = created.json()["id"]

    response = await client.delete(f"/customers/{id_}")
    assert response.status_code == 204

    # GET should now 404
    fetched = await client.get(f"/customers/{id_}")
    assert fetched.status_code == 404


@pytest.mark.asyncio
async def test_list_pagination(client: AsyncClient) -> None:
    # Create 5 customers
    for i in range(5):
        await client.post(
            "/customers",
            json={"name": f"User{i}", "email": f"user{i}@example.com"},
        )

    response = await client.get("/customers?page=0&size=2")
    assert response.status_code == 200
    body = response.json()
    assert len(body["content"]) == 2
    assert body["totalElements"] == 5
    assert body["totalPages"] == 3


@pytest.mark.asyncio
async def test_list_search_filters(client: AsyncClient) -> None:
    await client.post("/customers", json={"name": "Alice", "email": "alice@example.com"})
    await client.post("/customers", json={"name": "Bob", "email": "bob@example.com"})

    response = await client.get("/customers?search=alice")
    body = response.json()
    assert body["totalElements"] == 1
    assert body["content"][0]["name"] == "Alice"


@pytest.mark.asyncio
async def test_v2_returns_created_at(client: AsyncClient) -> None:
    await client.post(
        "/customers",
        json={"name": "Alice", "email": "alice@example.com"},
    )

    response = await client.get("/customers", headers={"X-API-Version": "2.0"})
    assert response.status_code == 200
    body = response.json()
    assert "createdAt" in body["content"][0]
    # v2 doesn't have deprecation
    assert "Deprecation" not in response.headers


@pytest.mark.asyncio
async def test_validation_rejects_invalid_email(client: AsyncClient) -> None:
    response = await client.post(
        "/customers",
        json={"name": "Bad", "email": "not-an-email"},
    )
    assert response.status_code == 422
