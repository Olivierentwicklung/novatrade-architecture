from datetime import datetime, timezone
from uuid import uuid4

import pytest

from novatrade.adapters.django.order_app.persistence.order_repository import (
    DjangoOrderRepository,
)
from novatrade.application.ports.order_repository_errors import OrderNotFound
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


@pytest.mark.django_db
def test_missing_order_is_translated_to_application_vocabulary() -> None:
    repository = DjangoOrderRepository()
    unknown_order_id = uuid4()

    with pytest.raises(OrderNotFound):
        repository.get(unknown_order_id)


@pytest.mark.django_db
def test_repository_lists_preserved_orders() -> None:
    repository = DjangoOrderRepository()
    first_order = Order()
    second_order = Order()

    repository.remember(first_order)
    repository.remember(second_order)

    retrieved_orders = repository.list()

    assert {order.id for order in retrieved_orders} == {
        first_order.id,
        second_order.id,
    }


@pytest.mark.django_db
def test_repository_preserves_order_creation_time() -> None:
    created_at = datetime(2026, 9, 5, 10, 30, tzinfo=timezone.utc)
    order = Order(created_at=created_at)
    repository = DjangoOrderRepository()

    repository.remember(order)

    retrieved_order = repository.get(order.id)

    assert retrieved_order.created_at == created_at
