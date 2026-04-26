"""create product table

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-26

Mirrors the Java Flyway V7 migration : product table with id (PK),
unique name, optional description (TEXT), unit_price NUMERIC(12,2)
CHECK >= 0, stock_quantity INTEGER CHECK >= 0, created_at + updated_at.

Part of the "augmenter la surface fonctionnelle" backlog (TASKS.md
2026-04-26). Independent entity — no FK dependencies — so ships first.

Schema parity with Java :
- BIGSERIAL → SQLAlchemy Integer + autoincrement (Postgres BIGINT under the hood)
- NUMERIC(12,2) → SQLAlchemy Numeric(12, 2) (BigDecimal-equivalent, no float rounding)
- CHECK constraints at the DB level (defense in depth alongside Pydantic validation)
- name UNIQUE + ix_product_name index (matches Java's idx_product_name)
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "product",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("stock_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("name", name="uq_product_name"),
        sa.CheckConstraint("unit_price >= 0", name="ck_product_unit_price_nonneg"),
        sa.CheckConstraint("stock_quantity >= 0", name="ck_product_stock_nonneg"),
    )
    op.create_index("ix_product_name", "product", ["name"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_product_name", table_name="product")
    op.drop_table("product")
