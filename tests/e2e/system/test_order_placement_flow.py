import pytest
from django.urls import reverse
from redis import Redis
from rest_framework import status
from rest_framework.test import APIClient

from novatrade.adapters.django.order_app.persistence.order_repository import (
    DjangoOrderRepository,
)
from novatrade.adapters.redis.event_channel import EVENT_CHANNEL
from novatrade.adapters.redis.event_receiver import RedisEventReceiver
from novatrade.domain.order import Order


@pytest.mark.django_db
def test_placing_order_publishes_event_for_processing_application() -> None:
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

    response = APIClient().post(
        reverse(
            "order-place",
            kwargs={"order_id": order.id},
        ),
        format="json",
    )

    event = RedisEventReceiver(redis).receive()

    assert response.status_code == status.HTTP_200_OK
    assert event is not None
    assert event.order_id == order.id
