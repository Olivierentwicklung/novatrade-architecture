import pytest

from novatrade.domain.order import CannotPlaceEmptyOrder, Order, OrderLine
from novatrade.domain.quantity import InvalidQuantity, Quantity


def test_empty_order_cannot_be_placed():
    order = Order()

    with pytest.raises(CannotPlaceEmptyOrder):
        order.place()


def test_product_can_be_added_to_order():
    order = Order()

    order.add_product(product_id="BOOK-123", quantity=2)

    assert order.lines == [
        OrderLine(
            product_id="BOOK-123",
            quantity=Quantity(2),
        )
    ]


def test_product_quantity_must_be_positive():
    order = Order()

    with pytest.raises(InvalidQuantity):
        order.add_product(
            product_id="BOOK-123",
            quantity=0,
        )


def test_product_quantity_can_be_changed():
    order = Order()

    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )

    order.change_quantity(
        product_id="BOOK-123",
        quantity=5,
    )

    assert order.quantity_for("BOOK-123") == 5


def test_changed_product_quantity_must_be_positive():
    order = Order()

    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )

    with pytest.raises(InvalidQuantity):
        order.change_quantity(
            product_id="BOOK-123",
            quantity=0,
        )


def test_order_exposes_its_lines_as_order_lines():
    order = Order()

    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )

    assert order.lines == [
        OrderLine(
            product_id="BOOK-123",
            quantity=Quantity(2),
        )
    ]
