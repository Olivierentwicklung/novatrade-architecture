from dataclasses import FrozenInstanceError

import pytest

from novatrade.domain.order import (
    CannotCancelCancelledOrder,
    CannotCancelConfirmedOrder,
    CannotCancelUnplacedOrder,
    CannotConfirmUnplacedOrder,
    CannotModifyPlacedOrder,
    CannotPlaceEmptyOrder,
    Order,
    OrderLine,
    OrderStatus,
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


def test_product_cannot_be_removed_after_order_is_placed() -> None:
    order = Order()

    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )

    order.place()

    with pytest.raises(CannotModifyPlacedOrder):
        order.remove_product(
            product_id="BOOK-123",
        )


def test_placed_order_can_be_confirmed() -> None:
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )
    order.place()

    order.confirm()

    assert order.status is OrderStatus.CONFIRMED


def test_unplaced_order_cannot_be_confirmed() -> None:
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )

    with pytest.raises(CannotConfirmUnplacedOrder):
        order.confirm()


def test_placed_order_can_be_cancelled() -> None:
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )
    order.place()

    order.cancel()

    assert order.status is OrderStatus.CANCELLED


def test_unplaced_order_cannot_be_cancelled() -> None:
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )

    with pytest.raises(CannotCancelUnplacedOrder):
        order.cancel()


def test_confirmed_order_cannot_be_cancelled() -> None:
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )
    order.place()
    order.confirm()

    with pytest.raises(CannotCancelConfirmedOrder):
        order.cancel()


def test_new_order_has_draft_status() -> None:
    order = Order()

    assert order.status is OrderStatus.DRAFT


def test_placing_order_changes_status_to_placed() -> None:
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )

    order.place()

    assert order.status is OrderStatus.PLACED


def test_confirming_order_changes_status_to_confirmed() -> None:
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )
    order.place()

    order.confirm()

    assert order.status is OrderStatus.CONFIRMED


def test_cancelling_order_changes_status_to_cancelled() -> None:
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )
    order.place()

    order.cancel()

    assert order.status is OrderStatus.CANCELLED


def test_cancelled_order_cannot_be_cancelled_again() -> None:
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )
    order.place()
    order.cancel()

    with pytest.raises(CannotCancelCancelledOrder):
        order.cancel()


def test_new_order_has_an_identity() -> None:
    order = Order()

    assert order.id is not None


def test_different_orders_have_different_identities() -> None:
    first_order = Order()
    first_order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )

    second_order = Order()
    second_order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )

    assert first_order.id != second_order.id
