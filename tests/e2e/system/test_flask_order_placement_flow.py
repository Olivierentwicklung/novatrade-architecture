import pytest
from redis import Redis

from novatrade.adapters.django.order_app.persistence.order_repository import (
    DjangoOrderRepository,
)
from novatrade.adapters.flask.app import create_app
from novatrade.adapters.redis.event_channel import EVENT_CHANNEL
from novatrade.adapters.redis.event_receiver import RedisEventReceiver
from novatrade.bootstrap.place_order import place_order_handler_factory
from novatrade.domain.order import Order


@pytest.mark.django_db
def test_flask_can_place_order_through_existing_application() -> None:
    redis = Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
    )
    redis.delete(EVENT_CHANNEL)

    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )
    DjangoOrderRepository().remember(order)

    app = create_app(
        place_order_handler=place_order_handler_factory(redis),
    )

    response = app.test_client().post(
        f"/orders/{order.id}/place",
    )

    event = RedisEventReceiver(redis).receive()

    assert response.status_code == 200
    assert event is not None
    assert event.order_id == order.id
