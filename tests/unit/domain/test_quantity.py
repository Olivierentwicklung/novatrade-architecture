import pytest
from novatrade.domain.quantity import InvalidQuantity, Quantity


def test_quantity_must_be_positive() -> None:
    with pytest.raises(InvalidQuantity):
        Quantity(0)
