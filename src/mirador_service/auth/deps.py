"""Auth FastAPI dependencies — current_user injection from Bearer token.

Usage in routers :
```
from mirador_service.auth.deps import current_user, require_role

@router.get("/protected")
async def protected(user: Annotated[AuthenticatedUser, Depends(current_user)]):
    return {"sub": user.username}

@router.post("/admin-only")
async def admin_only(user: Annotated[AuthenticatedUser, Depends(require_role("ROLE_ADMIN"))]):
    ...
```
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from mirador_service.auth.jwt import ACCESS_TOKEN, JwtError, decode_token
from mirador_service.config.settings import Settings, get_settings


@dataclass(frozen=True)
class AuthenticatedUser:
    """Lightweight value object surfaced to routers via DI."""

    username: str
    role: str


_bearer = HTTPBearer(auto_error=False)


def current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthenticatedUser:
    """Decode the Bearer token + return the authenticated user.

    Raises 401 on missing / invalid / expired / wrong-type token.
    """
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims = decode_token(settings.jwt, creds.credentials, expected_type=ACCESS_TOKEN)
    except JwtError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return AuthenticatedUser(username=claims["sub"], role=claims["role"])


def require_role(role: str) -> Callable[[AuthenticatedUser], AuthenticatedUser]:
    """Dependency factory — returns a sub-dependency that 403s if the user
    doesn't have the required role.

    Usage : `Depends(require_role("ROLE_ADMIN"))`
    """

    def _checker(user: Annotated[AuthenticatedUser, Depends(current_user)]) -> AuthenticatedUser:
        if user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {role}",
            )
        return user

    return _checker
