"""Middleware composition — single ``register_middleware(app)`` entry point.

Order matters (registration is inverse of execution per Starlette ASGI) :

Request flow  : SlowAPI → Prometheus → RequestId → CORS → handler
Response flow : handler → CORS → RequestId → Prometheus → SlowAPI

So we register :
1. CORS first (innermost, runs last on req / first on resp).
2. RequestIdMiddleware (so prometheus + slowapi see the request_id).
3. starlette-prometheus (records HTTP metrics, surfaced via /actuator/prometheus).
4. SlowAPI rate-limit handler last (outermost, rejects over-quota requests
   before the request hits any other middleware).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette_prometheus import PrometheusMiddleware

from mirador_service.middleware.request_id import RequestIdMiddleware

if TYPE_CHECKING:
    from fastapi import FastAPI

    from mirador_service.config.settings import Settings


# Global limiter — shared across the app. Default 60 requests per minute per
# IP — sane default for a demo, override per-route via @limiter.limit("10/minute").
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


def register_middleware(app: FastAPI, settings: Settings) -> None:
    """Wire all HTTP middleware onto the FastAPI app.

    Called from ``create_app`` after routers are mounted (middleware applies
    to every route registered before AND after, but registering after routers
    keeps the wiring close to the routers in the file).
    """
    # 1. CORS (innermost) — explicit allowlist, NOT wildcard (matches Java
    #    side's CORS config + global rule "no allowedHeaders: *").
    cors_origins = (
        ["http://localhost:4200", "http://localhost:5173"]
        if settings.dev_mode
        else []  # prod : populate via env-driven setting (TODO)
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    # 2. Request-ID — extracts X-Request-ID or generates UUID, binds to
    #    structlog context.
    app.add_middleware(RequestIdMiddleware)

    # 3. starlette-prometheus — records http_request_duration_seconds
    #    histogram + http_requests_total counter per (method, path_template,
    #    status_code). Exposed via /actuator/prometheus (which calls
    #    prometheus_client.generate_latest).
    app.add_middleware(PrometheusMiddleware)

    # 4. SlowAPI rate limit (outermost) — 60/min per IP by default. Returns
    #    429 + Retry-After when exceeded. Wired via app.state.limiter +
    #    exception handler.
    app.state.limiter = limiter
    # slowapi's handler narrows the second arg to RateLimitExceeded ; Starlette's
    # signature wants Exception (contravariant). Safe to ignore — the handler is
    # only invoked when the actual exception is RateLimitExceeded.
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
