"""TodoService — fetch todos from the JSONPlaceholder external API.

Mirror of Java's `TodoService` (Resilience4j circuit-breaker + retry +
empty-list fallback). Python equivalent : `tenacity` for retry-with-
exponential-backoff + a try/except wrapping for the empty-list fallback.

JSONPlaceholder is a public test API at https://jsonplaceholder.typicode.com.
Endpoint contract : `GET /users/{id}/todos` returns a JSON array of
`{ "userId": int, "id": int, "title": str, "completed": bool }`.

Resilience contract :
- Retry up to 3 times with exponential backoff (250ms → 500ms → 1s).
- Per-attempt timeout 5s.
- On final failure (network down, 5xx, timeout), return [] — graceful
  degradation. The customer page renders "No todos available" instead of
  a 500.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

JSONPLACEHOLDER_BASE_URL = "https://jsonplaceholder.typicode.com"
PER_ATTEMPT_TIMEOUT_S = 5.0


class TodoService:
    """Async client for JSONPlaceholder /todos."""

    def __init__(
        self,
        base_url: str = JSONPLACEHOLDER_BASE_URL,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url
        # Allow injecting a pre-configured client (tests use respx).
        self._client = client or httpx.AsyncClient(timeout=PER_ATTEMPT_TIMEOUT_S)

    async def get_todos(self, user_id: int) -> list[dict[str, Any]]:
        """Fetch todos for a user. Returns [] on any failure (graceful degradation)."""
        try:
            return await self._fetch_with_retry(user_id)
        except Exception as exc:
            logger.warning(
                "todo_fetch_failed user_id=%s reason=%s — returning empty list",
                user_id,
                exc,
            )
            return []

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.25, min=0.25, max=1.0),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True,
    )
    async def _fetch_with_retry(self, user_id: int) -> list[dict[str, Any]]:
        """Internal — issue the GET with tenacity retry. Reraises after 3 attempts."""
        url = f"{self._base_url}/users/{user_id}/todos"
        response = await self._client.get(url)
        response.raise_for_status()
        result: list[dict[str, Any]] = response.json()
        return result

    async def aclose(self) -> None:
        """Close the underlying HTTP client. Called from app.lifespan shutdown."""
        await self._client.aclose()
