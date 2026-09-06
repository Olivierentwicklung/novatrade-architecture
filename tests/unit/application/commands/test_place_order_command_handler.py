from datetime import datetime, timezone

from novatrade.application.commands.place_order_handler import (
    PlaceOrderCommandHandler,
)

from novatrade.adapters.in_memory.order_repository import (
    InMemoryOrderRepository,
)
from novatrade.application.commands.place_order import PlaceOrderCommand
from novatrade.application.ports.order_repository import OrderRepository
from novatrade.domain.events import OrderPlaced
from novatrade.domain.order import Order, OrderStatus

PLACED_AT = datetime(
    2026,
    9,
    6,
    18,
    30,
    tzinfo=timezone.utc,
)


class FakeEvents:
    def __init__(self) -> None:
        self.remembered_events: list[OrderPlaced] = []

    def remember(self, event: OrderPlaced) -> None:
        self.remembered_events.append(event)


class FakeWork:
    def __init__(self, orders: OrderRepository) -> None:
        self.orders = orders
        self.events = FakeEvents()

    def __enter__(self) -> "FakeWork":
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ) -> None:
        pass


class FakeEventPublisher:
    def __init__(self) -> None:
        self.published_events: list[OrderPlaced] = []

    def publish(self, event: OrderPlaced) -> None:
        self.published_events.append(event)


def test_place_order_command_is_handled() -> None:
    orders = InMemoryOrderRepository()
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=1,
    )
    orders.remember(order)

    work = FakeWork(orders)
    publisher = FakeEventPublisher()
    handler = PlaceOrderCommandHandler(
        work=work,
        publisher=publisher,
    )

    command = PlaceOrderCommand(
        order_id=order.id,
        placed_at=PLACED_AT,
    )

    handler.handle(command)

    placed_order = orders.get(order.id)

    assert placed_order.status is OrderStatus.PLACED
    assert publisher.published_events == [
        OrderPlaced(
            order_id=order.id,
            placed_at=PLACED_AT,
        )
    ]
