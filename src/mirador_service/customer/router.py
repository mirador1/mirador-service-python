"""Customer FastAPI router — v1 + v2 endpoints with header-based versioning.

Mirrors the Java `CustomerController` :
- GET /customers — list, with v1/v2 dispatch via `X-API-Version` header
- POST /customers — create
- GET /customers/{id} — read
- PUT /customers/{id} — replace
- PATCH /customers/{id} — partial update
- DELETE /customers/{id} — delete

The Java side uses Spring 7's native `@GetMapping(version=)` ; FastAPI doesn't
have an equivalent so we use header dispatch (same as the SB3 overlay's
manual approach).
"""

from __future__ import annotations

import math
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from mirador_service.customer.dtos import (
    CustomerCreate,
    CustomerPage,
    CustomerPageV2,
    CustomerPatch,
    CustomerResponse,
    CustomerResponseV2,
)
from mirador_service.customer.recent_buffer import RecentCustomerBuffer
from mirador_service.customer.repository import CustomerRepository
from mirador_service.db.base import get_db_session
from mirador_service.integration.redis_client import get_redis

router = APIRouter(prefix="/customers", tags=["Customer"])


# ── List (v1 + v2) ────────────────────────────────────────────────────────────


@router.get("", response_model=CustomerPage | CustomerPageV2)
async def list_customers(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    response: Response,
    page: Annotated[int, Query(ge=0, description="Zero-based page index")] = 0,
    size: Annotated[int, Query(ge=1, le=100, description="Page size, max 100")] = 20,
    search: Annotated[
        str | None,
        Query(description="Optional name/email filter (case-insensitive, partial)"),
    ] = None,
    api_version: Annotated[
        str,
        Header(alias="X-API-Version", description="API version : 1.0 or 2.0+"),
    ] = "1.0",
) -> CustomerPage | CustomerPageV2:
    """List customers paginated. Header `X-API-Version: 2.0` returns
    `CustomerResponseV2` (with `createdAt`)."""
    rows, total = await CustomerRepository.find_all(db, page=page, size=size, search=search)
    total_pages = math.ceil(total / size) if total > 0 else 0

    if api_version.startswith("2"):
        return CustomerPageV2(
            content=[CustomerResponseV2.model_validate(c) for c in rows],
            page=page,
            size=size,
            total_elements=total,
            total_pages=total_pages,
        )

    # v1 baseline — also surface deprecation header
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "2027-01-01T00:00:00Z"
    return CustomerPage(
        content=[CustomerResponse.model_validate(c) for c in rows],
        page=page,
        size=size,
        total_elements=total,
        total_pages=total_pages,
    )


# ── Create ────────────────────────────────────────────────────────────────────


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    body: CustomerCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> CustomerResponse:
    """Creates a new customer. 409 on duplicate email. Adds to recent buffer."""
    try:
        created = await CustomerRepository.create(db, name=body.name, email=body.email)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email already exists: {body.email}",
        ) from exc
    dto = CustomerResponse.model_validate(created)
    # Best-effort buffer add — Redis outage MUST NOT break the create flow.
    # Log only ; the next POST or background re-sync will recover the buffer.
    try:
        await RecentCustomerBuffer(redis).add(dto)
    except Exception as exc:
        # TODO : structured log via structlog when middleware is wired
        print(f"recent_buffer_add_failed id={dto.id} cause={exc}")
    return dto


@router.get("/recent", response_model=list[CustomerResponse])
async def get_recent_customers(
    redis: Annotated[Redis, Depends(get_redis)],
) -> list[CustomerResponse]:
    """Returns up to 10 most recently created customers from the Redis buffer.

    No DB hit — populated on each POST /customers, survives pod restarts,
    shared across replicas.
    """
    return await RecentCustomerBuffer(redis).get_recent()


# ── Read by ID ────────────────────────────────────────────────────────────────


@router.get("/{id_}", response_model=CustomerResponse)
async def get_customer(
    id_: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CustomerResponse:
    """Read a single customer. 404 if not found."""
    try:
        customer = await CustomerRepository.find_by_id_or_raise(db, id_)
    except NoResultFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return CustomerResponse.model_validate(customer)


# ── Replace (PUT) ─────────────────────────────────────────────────────────────


@router.put("/{id_}", response_model=CustomerResponse)
async def update_customer(
    id_: int,
    body: CustomerCreate,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CustomerResponse:
    """Replace name + email. 404 if not found ; 409 on email conflict."""
    try:
        updated = await CustomerRepository.update(db, id_, name=body.name, email=body.email)
    except NoResultFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email already exists: {body.email}",
        ) from exc
    return CustomerResponse.model_validate(updated)


# ── Patch ─────────────────────────────────────────────────────────────────────


@router.patch("/{id_}", response_model=CustomerResponse)
async def patch_customer(
    id_: int,
    body: CustomerPatch,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> CustomerResponse:
    """Partial update. 404 if not found ; 409 on email conflict."""
    try:
        patched = await CustomerRepository.patch(db, id_, name=body.name, email=body.email)
    except NoResultFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email already exists: {body.email}",
        ) from exc
    return CustomerResponse.model_validate(patched)


# ── Delete ────────────────────────────────────────────────────────────────────


@router.delete("/{id_}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_customer(
    id_: int,
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> Response:
    """Delete by id. 404 if not found."""
    try:
        await CustomerRepository.delete(db, id_)
    except NoResultFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
