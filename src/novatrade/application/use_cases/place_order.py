from datetime import datetime
from uuid import UUID

from novatrade.application.ports.committer import Committer
from novatrade.application.ports.order_repository import OrderRepository


def place_order(
    order_id: UUID,
    orders: OrderRepository,
    placed_at: datetime,
    committer: Committer,
) -> None:
    """Place and preserve the Order with the given identity."""
    order = orders.get(order_id)
    order.place(placed_at)
    orders.remember(order)
    committer.commit()
