"""Hypothesis property tests for Order invariants from shared ADR-0059.

Mirrors `mirador-service-java`'s `OrderInvariantsPropertyTest.java` :
each test captures one invariant, Hypothesis explores the input space,
shrinks failures to the smallest counter-example.

ADR-0059 reference :
https://gitlab.com/mirador1/mirador-service-shared/-/blob/main/docs/adr/0059-customer-order-product-data-model.md
"""

from __future__ import annotations

from decimal import Decimal

from hypothesis import given
from hypothesis import strategies as st

from mirador_service.order.order_line_models import OrderLine, OrderLineStatus
from mirador_service.order.totals import compute_total


def _line(quantity: int, unit_price: Decimal) -> OrderLine:
    """Factory for a transient (no DB) OrderLine — only the fields the
    invariant cares about. Avoids touching SQLAlchemy session state."""
    return OrderLine(
        order_id=1,
        product_id=1,
        quantity=quantity,
        unit_price_at_order=unit_price,
        status=OrderLineStatus.PENDING.value,
    )


# Strategy : a single OrderLine with positive quantity + positive price
# Bounds chosen to match the schema (Numeric(12,2), positive integer qty).
order_line = st.builds(
    _line,
    quantity=st.integers(min_value=1, max_value=1_000),
    unit_price=st.decimals(
        min_value=Decimal("0.01"),
        max_value=Decimal("99999.99"),
        places=2,
        allow_nan=False,
        allow_infinity=False,
    ),
)

order_lines = st.lists(order_line, min_size=0, max_size=20)


@given(order_lines)
def test_total_equals_sum_of_lines(lines: list[OrderLine]) -> None:
    """Invariant 1 : total == Σ(qty × unit_price_at_order).

    The production helper `compute_total` MUST agree with an independent
    recomputation. Diverging implementations would be caught here.
    """
    computed = compute_total(lines)
    expected = sum(
        (line.unit_price_at_order * Decimal(line.quantity) for line in lines),
        start=Decimal("0"),
    )
    assert computed == expected, f"compute_total({len(lines)} lines): {computed} != {expected}"


def test_total_empty_or_none_is_zero() -> None:
    """Boundary : empty list and None both yield Decimal('0').

    Captures the 'no lines = no money' contract explicitly."""
    assert compute_total([]) == Decimal("0")
    assert compute_total(None) == Decimal("0")


@given(order_lines)
def test_total_non_negative_for_valid_lines(lines: list[OrderLine]) -> None:
    """Business rule : total is never negative under valid (qty>0, price>0) inputs.

    A negative total would only emerge from a bug ; thousands of random
    inputs that never produce one give high confidence the rule holds."""
    total = compute_total(lines)
    assert total >= Decimal("0")


@given(st.lists(order_line, min_size=1, max_size=10))
def test_total_linear_in_quantity(lines: list[OrderLine]) -> None:
    """Pure-math property : doubling all quantities doubles the total.

    Verifies the implementation didn't sneak in non-linear behaviour
    (bulk discounts, quantity tiers) — those belong elsewhere if needed."""
    original_total = compute_total(lines)
    for line in lines:
        line.quantity = line.quantity * 2
    doubled_total = compute_total(lines)
    assert doubled_total == original_total * 2
