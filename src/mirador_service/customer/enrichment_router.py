"""Customer enrichment endpoint — `GET /customers/{id}/enrich` (Kafka request-reply).

Mirrors Java's `CustomerEnrichmentController.enrich` :
- 200 : enriched payload from the Kafka reply
- 404 : customer not found in DB
- 504 : Kafka reply did not arrive within the configured timeout

Kept in a separate router from the CRUD endpoints (split by concern, not
by resource — same pattern as Java's `CustomerEnrichmentController` vs
`CustomerController`). Resilience patterns + Kafka ownership stay
visible at a glance, separate from boring CRUD.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from mirador_service.config.settings import Settings, get_settings
from mirador_service.customer.repository import CustomerRepository
from mirador_service.db.base import get_db_session
from mirador_service.integration.todo_service import TodoService
from mirador_service.messaging.dtos import (
    CustomerEnrichRequest,
    EnrichedCustomerResponse,
)
from mirador_service.messaging.enrichment import EnrichmentService
from mirador_service.messaging.kafka_client import get_enrichment_service

router = APIRouter(prefix="/customers", tags=["Customer — enrichment"])

_todo_service: TodoService | None = None


def get_todo_service() -> TodoService:
    """FastAPI Depends provider — lazy singleton to share the httpx pool."""
    global _todo_service
    if _todo_service is None:
        _todo_service = TodoService()
    return _todo_service


@router.get("/{id_}/enrich", response_model=EnrichedCustomerResponse)
async def enrich_customer(
    id_: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    enrichment: Annotated[EnrichmentService, Depends(get_enrichment_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> EnrichedCustomerResponse:
    """Synchronous Kafka request-reply enrichment of a customer.

    Looks up the customer in DB (404 if missing), publishes a
    `CustomerEnrichRequest` to ``customer.enrich.request``, blocks on the
    correlated reply on ``customer.enrich.reply``, and returns the enriched
    payload (`displayName = "Name <email>"`).
    """
    try:
        customer = await CustomerRepository.find_by_id_or_raise(db, id_)
    except NoResultFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    request = CustomerEnrichRequest(
        id=customer.id,
        name=customer.name,
        email=customer.email,
    )
    try:
        reply = await enrichment.request_reply(request, timeout_s=float(settings.kafka.enrich_timeout_seconds))
    except TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=(
                f"Kafka enrichment did not reply within {settings.kafka.enrich_timeout_seconds}s for customer {id_}"
            ),
        ) from exc
    return EnrichedCustomerResponse(
        id=reply.id,
        name=reply.name,
        email=reply.email,
        display_name=reply.display_name,
    )


@router.get("/{id_}/todos")
async def get_customer_todos(
    id_: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    todos: Annotated[TodoService, Depends(get_todo_service)],
) -> list[dict[str, object]]:
    """Fetch todos for a customer from JSONPlaceholder (external API).

    Demonstrates graceful degradation : if the external API is down or
    flakes, returns an empty list — never 5xx. Customer page renders
    "No todos available" rather than an error banner.

    404 only on customer-not-found-in-our-DB (user expectation : we
    own the customer concept ; JSONPlaceholder only owns todos).
    """
    try:
        await CustomerRepository.find_by_id_or_raise(db, id_)
    except NoResultFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return await todos.get_todos(id_)
