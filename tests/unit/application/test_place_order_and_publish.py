from datetime import datetime, timezone
from types import TracebackType

import pytest

from novatrade.adapters.in_memory.order_repository import InMemoryOrderRepository
from novatrade.application.place_order_and_publish import (
    place_order_and_publish,
)
from novatrade.application.ports.order_repository import OrderRepository
from novatrade.domain.events import OrderPlaced
from novatrade.domain.order import Order

PLACED_AT = datetime(
    2026,
    9,
    4,
    10,
    30,
    tzinfo=timezone.utc,
)


class FakeEvents:
    def __init__(self) -> None:
        self.remembered_events: list[OrderPlaced] = []

    def remember(self, event: OrderPlaced) -> None:
        self.remembered_events.append(event)


class FakeEventPublisher:
    """Records Domain Events published by the Application."""

    def __init__(self) -> None:
        self.published_events: list[OrderPlaced] = []

    def publish(self, event: OrderPlaced) -> None:
        self.published_events.append(event)


class FakeWork:
    def __init__(self, orders: OrderRepository) -> None:
        self.orders = orders
        self.events = FakeEvents()

    def __enter__(self) -> "FakeWork":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass


class FailingWork(FakeWork):
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        raise RuntimeError("commit failed")


def test_successfully_placed_order_publishes_its_domain_events() -> None:
    orders = InMemoryOrderRepository()
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=1,
    )
    orders.remember(order)

    work = FakeWork(orders)
    publisher = FakeEventPublisher()

    place_order_and_publish(
        order_id=order.id,
        work=work,
        placed_at=PLACED_AT,
        publisher=publisher,
    )

    assert publisher.published_events == [
        OrderPlaced(
            order_id=order.id,
            placed_at=PLACED_AT,
        )
    ]


def test_failed_unit_of_work_does_not_publish_domain_events() -> None:
    orders = InMemoryOrderRepository()
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=1,
    )
    orders.remember(order)

    work = FailingWork(orders)
    publisher = FakeEventPublisher()

    with pytest.raises(RuntimeError, match="commit failed"):
        place_order_and_publish(
            order_id=order.id,
            work=work,
            placed_at=PLACED_AT,
            publisher=publisher,
        )

    assert publisher.published_events == []
