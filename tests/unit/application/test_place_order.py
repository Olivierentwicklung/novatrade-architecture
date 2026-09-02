from novatrade.application.place_order import place_order

from novatrade.domain.order import Order, OrderStatus


def test_application_can_place_order() -> None:
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )

    place_order(order)

    assert order.status is OrderStatus.PLACED
