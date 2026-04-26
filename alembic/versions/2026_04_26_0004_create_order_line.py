"""create order_line table

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-26

Mirrors Java's V9 migration : order_line entity carrying quantity +
unit_price_at_order snapshot + per-line status (PENDING/SHIPPED/REFUNDED).
ON DELETE CASCADE for order_id, RESTRICT for product_id.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "order_line",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "order_id",
            sa.Integer(),
            sa.ForeignKey("orders.id", ondelete="CASCADE", name="fk_order_line_order"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("product.id", ondelete="RESTRICT", name="fk_order_line_product"),
            nullable=False,
        ),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column(
            "unit_price_at_order",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("quantity > 0", name="ck_order_line_qty_positive"),
        sa.CheckConstraint("unit_price_at_order >= 0", name="ck_order_line_price_nonneg"),
        sa.CheckConstraint(
            "status IN ('PENDING', 'SHIPPED', 'REFUNDED')",
            name="ck_order_line_status",
        ),
    )
    op.create_index("ix_order_line_order_id", "order_line", ["order_id"])
    op.create_index("ix_order_line_product_id", "order_line", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_order_line_product_id", table_name="order_line")
    op.drop_index("ix_order_line_order_id", table_name="order_line")
    op.drop_table("order_line")
