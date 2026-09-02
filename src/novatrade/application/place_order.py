from uuid import UUID

from novatrade.application.orders import Orders


def place_order(order_id: UUID, orders: Orders) -> None:
    """Place the Order with the given identity."""
    order = orders.get(order_id)
    order.place()
