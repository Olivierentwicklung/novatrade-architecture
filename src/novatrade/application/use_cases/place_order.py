from datetime import datetime
from uuid import UUID

from novatrade.application.ports.unit_of_work import UnitOfWork


def place_order(
    order_id: UUID,
    work: UnitOfWork,
    placed_at: datetime,
) -> None:
    """Place and preserve the Order with the given identity."""
    with work:
        order = work.orders.get(order_id)
        order.place(placed_at)
        work.orders.remember(order)
