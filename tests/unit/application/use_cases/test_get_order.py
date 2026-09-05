from novatrade.application.use_cases.get_order import get_order

from novatrade.adapters.in_memory.order_repository import (
    InMemoryOrderRepository,
)
from novatrade.domain.order import Order


def test_get_order_returns_order_with_requested_identity() -> None:
    order = Order()
    orders = InMemoryOrderRepository()
    orders.remember(order)

    retrieved_order = get_order(
        order_id=order.id,
        orders=orders,
    )

    assert retrieved_order.id == order.id
