"""Password hashing — passlib bcrypt wrapper.

Bcrypt with strength 10 (matches Java mirror's BCryptPasswordEncoder default).
Never store plaintext passwords ; always hash on write, verify on auth.
"""

from __future__ import annotations

from passlib.context import CryptContext

# `bcrypt` scheme with default cost (10 rounds = ~80 ms on modern hardware,
# acceptable trade-off between brute-force resistance and login latency).
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Hash a plaintext password for storage."""
    result: str = _pwd_context.hash(plain)
    return result


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time comparison of plaintext against stored hash."""
    result: bool = _pwd_context.verify(plain, hashed)
    return result
