import pytest

from novatrade.adapters.django.persistence.repository import (
    DjangoOrderRepository,
)
from novatrade.domain.order import Order


@pytest.mark.django_db
def test_order_can_be_preserved_and_retrieved_by_identity() -> None:
    repository = DjangoOrderRepository()
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )

    order.place()

    repository.remember(order)

    retrieved_order = repository.get(order.id)

    assert retrieved_order.id == order.id
    assert retrieved_order.status == order.status
    assert retrieved_order.quantity_for("BOOK-123") == 2
