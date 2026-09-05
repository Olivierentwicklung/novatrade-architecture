from novatrade.application.ports.order_repository import OrderRepository
from novatrade.domain.order import Order


def list_orders(
    orders: OrderRepository,
) -> tuple[Order, ...]:
    """Return the latest 100 Orders."""
    return orders.latest(limit=100)
