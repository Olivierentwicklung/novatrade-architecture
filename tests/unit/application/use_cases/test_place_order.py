from datetime import datetime, timezone
from types import TracebackType
from uuid import UUID

import pytest

from novatrade.adapters.in_memory.order_repository import InMemoryOrderRepository
from novatrade.application.ports.order_repository import OrderRepository
from novatrade.application.use_cases.place_order import place_order
from novatrade.domain.events import OrderPlaced
from novatrade.domain.order import CannotPlaceEmptyOrder, Order, OrderStatus

PLACED_AT = datetime(
    2026,
    9,
    3,
    9,
    30,
    tzinfo=timezone.utc,
)


class SpyOrders:
    def __init__(self, order: Order) -> None:
        self.order = order
        self.remembered_order: Order | None = None

    def get(self, order_id: UUID) -> Order:
        assert order_id == self.order.id
        return self.order

    def remember(self, order: Order) -> None:
        self.remembered_order = order


class SpyEvents:
    def __init__(self) -> None:
        self.remembered_events: list[OrderPlaced] = []

    def remember(self, event: OrderPlaced) -> None:
        self.remembered_events.append(event)


class FakeWork:
    def __init__(
        self,
        orders: OrderRepository,
        events: SpyEvents | None = None,
    ) -> None:
        self.orders = orders
        self.events = events or SpyEvents()
        self.entered = False
        self.exited = False

    def __enter__(self) -> "FakeWork":
        self.entered = True
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.exited = True


def test_application_cannot_place_empty_order() -> None:
    orders = InMemoryOrderRepository()
    order = Order()
    orders.remember(order)
    work = FakeWork(orders)

    with pytest.raises(CannotPlaceEmptyOrder):
        place_order(
            order_id=order.id,
            work=work,
            placed_at=PLACED_AT,
        )


def test_application_can_place_remembered_order_by_identity() -> None:
    orders = InMemoryOrderRepository()
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )
    orders.remember(order)

    work = FakeWork(orders)

    place_order(
        order_id=order.id,
        work=work,
        placed_at=PLACED_AT,
    )

    placed_order = orders.get(order.id)

    assert placed_order.status is OrderStatus.PLACED


def test_placed_order_is_remembered() -> None:
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )
    orders = SpyOrders(order)

    work = FakeWork(orders)

    place_order(
        order_id=order.id,
        work=work,
        placed_at=PLACED_AT,
    )

    assert orders.remembered_order == order


def test_application_places_order_at_supplied_time() -> None:
    orders = InMemoryOrderRepository()
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )
    orders.remember(order)

    placed_at = datetime(
        2026,
        9,
        3,
        9,
        30,
        tzinfo=timezone.utc,
    )

    work = FakeWork(orders)

    place_order(
        order_id=order.id,
        work=work,
        placed_at=PLACED_AT,
    )

    placed_order = orders.get(order.id)

    assert placed_order.placed_at == placed_at


def test_placing_order_uses_one_persistence_boundary() -> None:
    orders = InMemoryOrderRepository()
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=1,
    )
    orders.remember(order)

    work = FakeWork(orders)

    place_order(
        order_id=order.id,
        work=work,
        placed_at=PLACED_AT,
    )

    placed_order = work.orders.get(order.id)

    assert placed_order.status is OrderStatus.PLACED


def test_placing_order_runs_inside_unit_of_work() -> None:
    orders = InMemoryOrderRepository()
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=1,
    )
    orders.remember(order)

    work = FakeWork(orders)

    place_order(
        order_id=order.id,
        work=work,
        placed_at=PLACED_AT,
    )

    assert work.entered
    assert work.exited


def test_placing_order_returns_produced_domain_events() -> None:
    orders = InMemoryOrderRepository()
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=1,
    )
    orders.remember(order)

    work = FakeWork(orders)

    events = place_order(
        order_id=order.id,
        work=work,
        placed_at=PLACED_AT,
    )

    assert events == (
        OrderPlaced(
            order_id=order.id,
            placed_at=PLACED_AT,
        ),
    )


def test_placing_order_preserves_produced_domain_events() -> None:
    orders = InMemoryOrderRepository()

    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=1,
    )
    orders.remember(order)

    events = SpyEvents()
    work = FakeWork(
        orders=orders,
        events=events,
    )

    place_order(
        order_id=order.id,
        work=work,
        placed_at=PLACED_AT,
    )

    assert events.remembered_events == [
        OrderPlaced(
            order_id=order.id,
            placed_at=PLACED_AT,
        )
    ]
