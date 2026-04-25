"""FastAPI app factory + lifespan management.

Mirrors the Spring Boot 4 application class : declares the app, wires startup/
shutdown hooks (DB pool, Kafka producer/consumer, OTel SDK), registers
middleware (CORS, request ID, structured logging), and mounts routers.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from mirador_service import __version__
from mirador_service.api.actuator import router as actuator_router
from mirador_service.auth.router import router as auth_router
from mirador_service.config.settings import get_settings
from mirador_service.customer.router import router as customer_router
from mirador_service.db.base import reset_engine
from mirador_service.integration.redis_client import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup + shutdown hooks.

    Order matters :
    1. OTel SDK init FIRST so subsequent setup is traced.
    2. DB pool open (lazy via get_engine() on first session request).
    3. Redis client open.
    4. Kafka producer/consumer start.
    5. Yield → serve requests.
    6. Reverse on shutdown.
    """
    # TODO : init OTel SDK + Redis client + Kafka producer/consumer
    yield
    # Shutdown : close in reverse-startup order
    await close_redis()
    await reset_engine()
    # TODO : close Kafka


def create_app() -> FastAPI:
    """App factory — used by uvicorn (`mirador_service.app:app`) and tests."""
    # Fail-fast on broken env config at app construction time vs first request
    # (same pattern as Spring's @PostConstruct on @Configuration beans).
    get_settings()
    app = FastAPI(
        title="Mirador Customer Service (Python)",
        version=__version__,
        description="Python mirror of the Java mirador-service.",
        lifespan=lifespan,
    )

    # TODO : register CORS, request-id, logging, rate-limit middleware
    app.include_router(actuator_router)
    app.include_router(auth_router)
    app.include_router(customer_router)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {"service": "mirador-service-python", "version": __version__}

    return app


# Module-level instance for uvicorn `mirador_service.app:app`
app = create_app()


def run() -> None:
    """Console script entry point — `uv run mirador-service`."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "mirador_service.app:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.dev_mode,
        log_level="info",
    )


if __name__ == "__main__":
    run()
