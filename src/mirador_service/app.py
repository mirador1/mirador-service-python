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
from mirador_service.config.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup + shutdown hooks.

    Order matters :
    1. OTel SDK init FIRST so subsequent setup is traced.
    2. DB pool open.
    3. Redis client open.
    4. Kafka producer/consumer start.
    5. Yield → serve requests.
    6. Reverse on shutdown.
    """
    # TODO : init OTel SDK
    # TODO : open DB pool, Redis client, Kafka producer/consumer
    yield
    # TODO : close in reverse order


def create_app() -> FastAPI:
    """App factory — used by uvicorn (`mirador_service.app:app`) and tests."""
    # settings is intentionally instantiated here (even if unused at this stage)
    # to fail-fast if env config is broken at app construction time vs first
    # request — same pattern as Spring's @PostConstruct on @Configuration beans.
    get_settings()
    app = FastAPI(
        title="Mirador Customer Service (Python)",
        version=__version__,
        description="Python mirror of the Java mirador-service.",
        lifespan=lifespan,
    )

    # TODO : register CORS, request-id, logging, rate-limit middleware
    # TODO : mount routers (auth, customer, actuator)

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
