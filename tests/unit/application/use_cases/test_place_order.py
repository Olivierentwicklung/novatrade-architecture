from datetime import datetime, timezone
from uuid import UUID

import pytest

from novatrade.adapters.in_memory.order_repository import InMemoryOrderRepository
from novatrade.application.use_cases.place_order import place_order
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


class SpyCommitter:
    def __init__(self) -> None:
        self.committed = False

    def commit(self) -> None:
        self.committed = True


class FakeCommitter:
    def commit(self) -> None:
        pass


class FakeWork:
    def __init__(self, orders: InMemoryOrderRepository) -> None:
        self.orders = orders
        self.committed = False

    def commit(self) -> None:
        self.committed = True


def test_application_cannot_place_empty_order() -> None:
    orders = InMemoryOrderRepository()
    order = Order()
    orders.remember(order)

    with pytest.raises(CannotPlaceEmptyOrder):
        place_order(
            order_id=order.id,
            orders=orders,
            placed_at=PLACED_AT,
            committer=FakeCommitter(),
        )


def test_application_can_place_remembered_order_by_identity() -> None:
    orders = InMemoryOrderRepository()
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )
    orders.remember(order)

    place_order(
        order_id=order.id,
        orders=orders,
        placed_at=PLACED_AT,
        committer=FakeCommitter(),
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

    place_order(
        order_id=order.id,
        orders=orders,
        placed_at=PLACED_AT,
        committer=FakeCommitter(),
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

    place_order(
        order_id=order.id,
        orders=orders,
        placed_at=placed_at,
        committer=FakeCommitter(),
    )

    placed_order = orders.get(order.id)

    assert placed_order.placed_at == placed_at


def test_placing_order_commits_the_application_operation() -> None:
    orders = InMemoryOrderRepository()
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=1,
    )
    orders.remember(order)

    committer = SpyCommitter()

    place_order(
        order_id=order.id,
        orders=orders,
        placed_at=PLACED_AT,
        committer=committer,
    )

    assert committer.committed


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
    assert work.committed
