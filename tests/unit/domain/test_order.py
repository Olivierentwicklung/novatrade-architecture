from dataclasses import FrozenInstanceError

import pytest

from novatrade.domain.order import (
    CannotModifyPlacedOrder,
    CannotPlaceEmptyOrder,
    Order,
    OrderLine,
)
from novatrade.domain.quantity import InvalidQuantity, Quantity


def test_empty_order_cannot_be_placed():
    order = Order()

    with pytest.raises(CannotPlaceEmptyOrder):
        order.place()


def test_product_can_be_added_to_order():
    order = Order()

    order.add_product(product_id="BOOK-123", quantity=2)

    assert order.lines == (
        OrderLine(
            product_id="BOOK-123",
            quantity=Quantity(2),
        ),
    )


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

    assert order.lines == (
        OrderLine(
            product_id="BOOK-123",
            quantity=Quantity(2),
        ),
    )


def test_adding_same_product_again_increases_its_quantity() -> None:
    order = Order()

    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )

    order.add_product(
        product_id="BOOK-123",
        quantity=3,
    )

    assert order.lines == (
        OrderLine(
            product_id="BOOK-123",
            quantity=Quantity(5),
        ),
    )


def test_order_lines_with_same_values_are_equal() -> None:
    first = OrderLine(
        product_id="BOOK-123",
        quantity=Quantity(2),
    )
    second = OrderLine(
        product_id="BOOK-123",
        quantity=Quantity(2),
    )

    assert first == second


def test_order_line_is_immutable() -> None:
    line = OrderLine(
        product_id="BOOK-123",
        quantity=Quantity(2),
    )

    with pytest.raises(FrozenInstanceError):
        line.quantity = Quantity(5)  # type:ignore


def test_product_cannot_be_added_after_order_is_placed() -> None:
    order = Order()

    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )

    order.place()

    with pytest.raises(CannotModifyPlacedOrder):
        order.add_product(
            product_id="PEN-456",
            quantity=1,
        )


def test_product_quantity_cannot_be_changed_after_order_is_placed() -> None:
    order = Order()

    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )

    order.place()

    with pytest.raises(CannotModifyPlacedOrder):
        order.change_quantity(
            product_id="BOOK-123",
            quantity=5,
        )


def test_order_exposes_lines_as_immutable_collection() -> None:
    order = Order()

    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )

    assert order.lines == (
        OrderLine(
            product_id="BOOK-123",
            quantity=Quantity(2),
        ),
    )

    assert isinstance(order.lines, tuple)


def test_product_can_be_removed_from_order() -> None:
    order = Order()

    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )

    order.remove_product(
        product_id="BOOK-123",
    )

    assert order.lines == ()
