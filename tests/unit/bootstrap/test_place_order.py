from fakeredis import FakeRedis
from novatrade.bootstrap.place_order import (
    place_order_handler_factory,
)

from novatrade.application.commands.place_order_handler import (
    PlaceOrderCommandHandler,
)


def test_place_order_handler_can_be_assembled() -> None:
    redis = FakeRedis()

    handler = place_order_handler_factory(redis=redis)

    assert isinstance(handler, PlaceOrderCommandHandler)
