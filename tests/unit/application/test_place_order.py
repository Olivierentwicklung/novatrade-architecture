import pytest

from novatrade.application.orders import Orders
from novatrade.application.place_order import place_order
from novatrade.domain.order import CannotPlaceEmptyOrder, Order, OrderStatus


def test_application_can_place_order() -> None:
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )

    place_order(order)

    assert order.status is OrderStatus.PLACED


def test_application_cannot_place_empty_order() -> None:
    order = Order()

    with pytest.raises(CannotPlaceEmptyOrder):
        place_order(order)


def test_application_can_place_remembered_order_by_identity() -> None:
    orders = Orders()
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )
    orders.remember(order)

    place_order(
        order_id=order.id,
        orders=orders,
    )

    assert order.status is OrderStatus.PLACED
