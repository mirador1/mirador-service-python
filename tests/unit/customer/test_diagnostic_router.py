"""Diagnostic scenario endpoint tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_slow_query_completes_within_requested_window(
    client: AsyncClient,
) -> None:
    response = await client.get("/customers/diagnostic/slow-query?seconds=1")
    assert response.status_code == 200
    body = response.json()
    assert body["scenario"] == "slow-query"
    assert body["requested_seconds"] == 1
    # actual_seconds should be ≥ 1 (sleep is at least the requested duration)
    assert body["actual_seconds"] >= 1.0


@pytest.mark.asyncio
async def test_slow_query_validates_bounds(client: AsyncClient) -> None:
    """seconds must be 1-10."""
    too_low = await client.get("/customers/diagnostic/slow-query?seconds=0")
    assert too_low.status_code == 422
    too_high = await client.get("/customers/diagnostic/slow-query?seconds=11")
    assert too_high.status_code == 422


@pytest.mark.asyncio
async def test_db_failure_returns_500(client: AsyncClient) -> None:
    response = await client.get("/customers/diagnostic/db-failure")
    assert response.status_code == 500
    assert "db-failure" in response.json()["detail"]


@pytest.mark.asyncio
async def test_kafka_timeout_returns_504(client: AsyncClient) -> None:
    response = await client.get("/customers/diagnostic/kafka-timeout")
    assert response.status_code == 504
    assert "kafka-timeout" in response.json()["detail"]
