"""BioService — generates a customer bio via local Ollama LLM.

Mirror of Java's BioService (Resilience4j circuit-breaker + retry +
fallback). Python equivalent : `tenacity` for retry-with-exponential-
backoff + a try/except fallback returning a synthetic bio on Ollama
outage.

Ollama runs locally (or in the dev-stack docker-compose `llm` profile)
at http://localhost:11434. POST /api/generate with prompt → streamed
response (we use stream=False for simpler handling).

Resilience contract :
- Retry up to 2 times (LLM calls are slow ; 3 attempts of 30s = 90s
  wall-clock worst case).
- Per-attempt timeout 30s (LLM cold start can be 5-10s).
- On final failure, return synthetic bio "<Name> is a customer at our
  service. Bio currently unavailable." — graceful degradation.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2"
PER_ATTEMPT_TIMEOUT_S = 30.0


class BioService:
    """Async client for Ollama /api/generate."""

    def __init__(
        self,
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_MODEL,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url
        self._model = model
        self._client = client or httpx.AsyncClient(timeout=PER_ATTEMPT_TIMEOUT_S)

    async def generate_bio(self, name: str, email: str) -> str:
        """Generate a short professional bio. Returns synthetic fallback on failure."""
        prompt = (
            f"Write a single concise (≤ 30 words) professional bio for a customer "
            f"named {name}, email {email}. Plain prose, no greeting, no markdown."
        )
        try:
            return await self._generate_with_retry(prompt)
        except Exception as exc:
            logger.warning(
                "bio_generate_failed name=%s reason=%s — synthetic fallback",
                name,
                exc,
            )
            return f"{name} is a customer at our service. Bio currently unavailable."

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1.0, min=1.0, max=5.0),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True,
    )
    async def _generate_with_retry(self, prompt: str) -> str:
        response = await self._client.post(
            f"{self._base_url}/api/generate",
            json={
                "model": self._model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 80},
            },
        )
        response.raise_for_status()
        body: dict[str, Any] = response.json()
        text = str(body.get("response", "")).strip()
        if not text:
            raise ValueError("Ollama returned empty response")
        return text

    async def aclose(self) -> None:
        """Close the underlying HTTP client. Called from app.lifespan shutdown."""
        await self._client.aclose()
