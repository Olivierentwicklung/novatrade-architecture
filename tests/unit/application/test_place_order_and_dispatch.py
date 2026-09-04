from datetime import datetime, timezone
from types import TracebackType

from novatrade.adapters.in_memory.order_repository import InMemoryOrderRepository
from novatrade.application.event_dispatcher import EventDispatcher
from novatrade.application.place_order_and_dispatch import place_order_and_dispatch
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


class FakeWork:
    def __init__(self, orders: OrderRepository) -> None:
        self.orders = orders

    def __enter__(self) -> "FakeWork":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        pass


def test_successfully_placed_order_dispatches_its_domain_events() -> None:
    orders = InMemoryOrderRepository()
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=1,
    )
    orders.remember(order)

    work = FakeWork(orders)

    received_events: list[OrderPlaced] = []

    def reaction(event: OrderPlaced) -> None:
        received_events.append(event)

    dispatcher = EventDispatcher(
        reactions={
            OrderPlaced: (reaction,),
        }
    )

    place_order_and_dispatch(
        order_id=order.id,
        work=work,
        placed_at=PLACED_AT,
        dispatcher=dispatcher,
    )

    assert received_events == [
        OrderPlaced(
            order_id=order.id,
            placed_at=PLACED_AT,
        )
    ]
