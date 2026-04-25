"""Redis-backed ring buffer for recent customers.

Mirror of Java's RecentCustomerBuffer :
- LPUSH on add()
- LTRIM to MAX_SIZE entries
- LRANGE on get_recent()

Stored as JSON strings (Pydantic serialised). Survives pod restarts +
shared across replicas (single Redis = single source of truth).
"""

from __future__ import annotations

import json

from redis.asyncio import Redis

from mirador_service.customer.dtos import CustomerResponse

KEY = "customer-service:recent:customers"
MAX_SIZE = 10


class RecentCustomerBuffer:
    """Async Redis-backed ring buffer."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def add(self, customer: CustomerResponse) -> None:
        """Prepend + trim. LPUSH + LTRIM are not atomic together but the
        worst-case race is a list of MAX_SIZE+1 briefly — acceptable for a
        non-critical display buffer."""
        payload = customer.model_dump_json()
        await self._redis.lpush(KEY, payload)  # type: ignore[misc]
        await self._redis.ltrim(KEY, 0, MAX_SIZE - 1)  # type: ignore[misc]

    async def get_recent(self) -> list[CustomerResponse]:
        """Return up to MAX_SIZE recent customers, newest first."""
        raw: list[bytes | str] = await self._redis.lrange(KEY, 0, MAX_SIZE - 1)  # type: ignore[misc]
        result: list[CustomerResponse] = []
        for item in raw:
            try:
                if isinstance(item, bytes):
                    item = item.decode("utf-8")
                result.append(CustomerResponse.model_validate(json.loads(item)))
            except json.JSONDecodeError, ValueError:
                # Malformed entry : skip silently — the buffer is best-effort.
                continue
        return result

    async def size(self) -> int:
        """Return current buffer size (for Prometheus gauge)."""
        return int(await self._redis.llen(KEY))  # type: ignore[misc]
