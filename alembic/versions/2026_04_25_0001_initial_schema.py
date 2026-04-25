"""initial schema — customer, app_user, refresh_token

Revision ID: 0001
Revises:
Create Date: 2026-04-25

Mirrors the Java Flyway baseline V1 :
- customer (PK + name + unique email + created_at)
- app_user (PK + unique username + bcrypt password_hash + role + enabled)
- refresh_token (PK + unique token + username FK + expires_at + revoked + created_at)

Indexes mirror Java side :
- customer.email : unique + indexed (email is the natural lookup key)
- app_user.username : unique + indexed (auth login lookup)
- refresh_token.token : unique + indexed (rotation + revocation lookup)
- refresh_token.username : indexed (cascade revoke on logout-all)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "customer",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("email", name="uq_customer_email"),
    )
    op.create_index("ix_customer_email", "customer", ["email"], unique=True)

    op.create_table(
        "app_user",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        # role string ; matches Java's String role (no enum constraint, room
        # for future fine-grained roles without a migration).
        sa.Column("role", sa.String(length=32), nullable=False, server_default="USER"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("username", name="uq_app_user_username"),
    )
    op.create_index("ix_app_user_username", "app_user", ["username"], unique=True)

    op.create_table(
        "refresh_token",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("token", sa.String(length=512), nullable=False),
        # username (NOT user_id FK) : tokens reference users by username for
        # symmetry with the JWT payload's `sub` claim. Cascade on user delete
        # is handled at the application level (logout = delete tokens by username).
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("token", name="uq_refresh_token_token"),
    )
    op.create_index("ix_refresh_token_token", "refresh_token", ["token"], unique=True)
    op.create_index("ix_refresh_token_username", "refresh_token", ["username"])


def downgrade() -> None:
    # Reverse-order drop : refresh_token (no FKs IN), app_user, customer.
    op.drop_index("ix_refresh_token_username", table_name="refresh_token")
    op.drop_index("ix_refresh_token_token", table_name="refresh_token")
    op.drop_table("refresh_token")
    op.drop_index("ix_app_user_username", table_name="app_user")
    op.drop_table("app_user")
    op.drop_index("ix_customer_email", table_name="customer")
    op.drop_table("customer")
