from novatrade.domain.order import Order


def place_order(order: Order) -> None:
    """Execute the use case of placing an Order."""
    order.place()
