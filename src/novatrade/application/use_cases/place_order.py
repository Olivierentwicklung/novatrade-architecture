from uuid import UUID

from novatrade.application.ports.order_repository import OrderRepository


def place_order(order_id: UUID, orders: OrderRepository) -> None:
    """Place and preserve the Order with the given identity."""
    order = orders.get(order_id)
    order.place()
    orders.remember(order)
