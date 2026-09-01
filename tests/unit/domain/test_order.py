import pytest

from novatrade.domain.order import CannotPlaceEmptyOrder, Order


def test_empty_order_cannot_be_placed():
    order = Order()

    with pytest.raises(CannotPlaceEmptyOrder):
        order.place()
