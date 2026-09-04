from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from novatrade.domain.events import OrderPlaced
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

PLACED_AT = datetime(
    2026,
    9,
    3,
    9,
    30,
    tzinfo=timezone.utc,
)


def test_empty_order_cannot_be_placed():
    order = Order()

    with pytest.raises(CannotPlaceEmptyOrder):
        order.place(PLACED_AT)


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

    order.place(PLACED_AT)

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

    order.place(PLACED_AT)

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

    order.place(PLACED_AT)

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
    order.place(PLACED_AT)

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
    order.place(PLACED_AT)

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
    order.place(PLACED_AT)
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

    order.place(PLACED_AT)

    assert order.status is OrderStatus.PLACED


def test_confirming_order_changes_status_to_confirmed() -> None:
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )
    order.place(PLACED_AT)

    order.confirm()

    assert order.status is OrderStatus.CONFIRMED


def test_cancelling_order_changes_status_to_cancelled() -> None:
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )
    order.place(PLACED_AT)

    order.cancel()

    assert order.status is OrderStatus.CANCELLED


def test_cancelled_order_cannot_be_cancelled_again() -> None:
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )
    order.place(PLACED_AT)
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


def test_order_can_be_created_with_existing_identity() -> None:
    existing_id = uuid4()

    order = Order(order_id=existing_id)

    assert order.id == existing_id


def test_orders_with_same_identity_are_equal() -> None:
    existing_id = uuid4()

    first_order = Order(order_id=existing_id)
    second_order = Order(order_id=existing_id)

    assert first_order == second_order


def test_orders_with_same_contents_but_different_identities_are_not_equal() -> None:
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

    assert first_order != second_order


def test_placing_order_records_when_it_was_placed() -> None:
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=1,
    )

    order.place(PLACED_AT)

    assert order.placed_at == PLACED_AT


def test_placed_order_can_be_reconstituted_without_placing_it_again() -> None:
    order_id = UUID("12345678-1234-5678-1234-567812345678")

    order = Order.reconstitute(
        order_id=order_id,
        status=OrderStatus.PLACED,
        placed_at=PLACED_AT,
        lines=(
            OrderLine(
                product_id="BOOK-123",
                quantity=Quantity(2),
            ),
        ),
    )

    assert order.id == order_id
    assert order.status is OrderStatus.PLACED
    assert order.placed_at == PLACED_AT
    assert order.quantity_for("BOOK-123") == 2


def test_placing_order_records_that_order_was_placed() -> None:
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=1,
    )

    placed_at = datetime(2026, 9, 4, 10, 30)

    order.place(placed_at)

    assert order.events == (
        OrderPlaced(
            order_id=order.id,
            placed_at=placed_at,
        ),
    )


def test_recorded_placement_fact_has_business_meaning() -> None:
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=1,
    )

    placed_at = datetime(2026, 9, 4, 10, 30)

    order.place(placed_at)

    placement = order.events[0]

    assert placement.order_id == order.id
    assert placement.placed_at == placed_at


def test_reconstituting_placed_order_does_not_record_new_placement_fact() -> None:
    order_id = uuid4()
    placed_at = datetime(2026, 9, 4, 10, 30)

    order = Order.reconstitute(
        order_id=order_id,
        status=OrderStatus.PLACED,
        placed_at=placed_at,
        lines=(
            OrderLine(
                product_id="BOOK-123",
                quantity=Quantity(1),
            ),
        ),
    )

    assert order.events == ()


def test_placing_order_records_domain_event() -> None:
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=1,
    )

    placed_at = datetime(2026, 9, 4, 10, 30)

    order.place(placed_at)

    assert order.events == (
        OrderPlaced(
            order_id=order.id,
            placed_at=placed_at,
        ),
    )


def test_recorded_domain_events_can_be_collected() -> None:
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=1,
    )

    placed_at = datetime(2026, 9, 4, 10, 30)

    order.place(placed_at)

    events = order.collect_events()

    assert events == (
        OrderPlaced(
            order_id=order.id,
            placed_at=placed_at,
        ),
    )
    assert order.events == ()
