from novatrade.application.in_memory_order_repository import InMemoryOrderRepository
from novatrade.domain.order import Order


def test_remembered_order_can_be_retrieved_by_identity() -> None:
    orders = InMemoryOrderRepository()
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )

    orders.remember(order)

    retrieved_order = orders.get(order.id)

    assert retrieved_order == order
