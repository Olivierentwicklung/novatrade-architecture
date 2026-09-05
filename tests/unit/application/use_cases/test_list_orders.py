from novatrade.adapters.in_memory.order_repository import (
    InMemoryOrderRepository,
)
from novatrade.application.use_cases.list_orders import list_orders
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


from datetime import datetime, timedelta, timezone


def test_list_orders_returns_latest_100_orders() -> None:
    base_time = datetime(2026, 9, 5, 10, 0, tzinfo=timezone.utc)

    orders = InMemoryOrderRepository()

    created_orders = [
        Order(created_at=base_time + timedelta(minutes=index)) for index in range(101)
    ]

    for order in created_orders:
        orders.remember(order)

    retrieved_orders = list_orders(orders=orders)

    assert len(retrieved_orders) == 100
    assert retrieved_orders[0].id == created_orders[-1].id
    assert retrieved_orders[-1].id == created_orders[1].id
