from dataclasses import FrozenInstanceError

import pytest

from novatrade.domain.quantity import InvalidQuantity, Quantity


def test_zero_quantity_is_invalid() -> None:
    with pytest.raises(InvalidQuantity):
        Quantity(0)


def test_positive_quantity_is_valid() -> None:
    quantity = Quantity(2)

    assert quantity.value == 2


def test_negative_quantity_is_invalid() -> None:
    with pytest.raises(InvalidQuantity):
        Quantity(-1)


def test_non_integer_quantity_is_invalid() -> None:
    with pytest.raises(InvalidQuantity):
        Quantity(1.5)  # type: ignore[arg-type]


def test_boolean_quantity_is_invalid() -> None:
    with pytest.raises(InvalidQuantity):
        Quantity(True)


def test_quantities_with_same_value_are_equal() -> None:
    assert Quantity(2) == Quantity(2)


def test_quantity_is_immutable() -> None:
    quantity = Quantity(2)

    with pytest.raises(FrozenInstanceError):
        quantity.value = 5  # type: ignore[misc]
