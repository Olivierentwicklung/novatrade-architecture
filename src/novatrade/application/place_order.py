from uuid import UUID

from novatrade.application.order_reader import OrderReader


def place_order(order_id: UUID, orders: OrderReader) -> None:
    """Place the Order with the given identity."""
    order = orders.get(order_id)
    order.place()
