from uuid import UUID

from novatrade.application.ports.order_repository import OrderRepository
from novatrade.domain.order import Order


def get_order(
    order_id: UUID,
    orders: OrderRepository,
) -> Order:
    """Return the Order with the requested identity."""
    return orders.get(order_id)
