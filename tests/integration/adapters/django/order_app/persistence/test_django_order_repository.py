from datetime import datetime, timezone

import pytest

from novatrade.adapters.django.order_app.persistence.order_repository import (
    DjangoOrderRepository,
)
from novatrade.domain.order import Order

PLACED_AT = datetime(
    2026,
    9,
    3,
    9,
    30,
    tzinfo=timezone.utc,
)


@pytest.mark.django_db
def test_order_can_be_preserved_and_retrieved_by_identity() -> None:
    repository = DjangoOrderRepository()
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )

    order.place(PLACED_AT)

    repository.remember(order)

    retrieved_order = repository.get(order.id)

    assert retrieved_order.id == order.id
    assert retrieved_order.status == order.status
    assert retrieved_order.quantity_for("BOOK-123") == 2
    assert retrieved_order.placed_at == PLACED_AT
