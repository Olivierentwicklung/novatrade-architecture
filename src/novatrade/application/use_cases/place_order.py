from datetime import datetime
from uuid import UUID

from novatrade.application.ports.unit_of_work import UnitOfWork
from novatrade.domain.events import OrderPlaced


def place_order(
    order_id: UUID,
    work: UnitOfWork,
    placed_at: datetime,
) -> tuple[OrderPlaced, ...]:
    """Place and preserve the Order and the Domain Events it produces."""
    with work:
        order = work.orders.get(order_id)
        order.place(placed_at)
        work.orders.remember(order)

        events = order.collect_events()

        for event in events:
            work.events.remember(event)

        return events
