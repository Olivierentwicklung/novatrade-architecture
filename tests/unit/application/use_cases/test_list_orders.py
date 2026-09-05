from novatrade.application.use_cases.list_orders import list_orders

from novatrade.adapters.in_memory.order_repository import (
    InMemoryOrderRepository,
)
from novatrade.domain.order import Order


def test_list_orders_returns_existing_orders() -> None:
    first_order = Order()
    second_order = Order()

    orders = InMemoryOrderRepository()
    orders.remember(first_order)
    orders.remember(second_order)

    retrieved_orders = list_orders(orders=orders)

    assert {order.id for order in retrieved_orders} == {
        first_order.id,
        second_order.id,
    }
