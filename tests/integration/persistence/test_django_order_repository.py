from novatrade.adapters.persistence.django_order_repository import (
    DjangoOrderRepository,
)

from novatrade.domain.order import Order


def test_order_can_be_preserved_and_retrieved_by_identity() -> None:
    repository = DjangoOrderRepository()
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )

    repository.remember(order)

    retrieved_order = repository.get(order.id)

    assert retrieved_order == order
