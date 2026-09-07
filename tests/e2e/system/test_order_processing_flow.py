from datetime import datetime
from uuid import UUID

import pytest
from django.urls import reverse
from redis import Redis
from rest_framework import status
from rest_framework.test import APIClient

from novatrade.adapters.django.order_app.persistence.order_repository import (
    DjangoOrderRepository,
)
from novatrade.adapters.redis.event_channel import EVENT_CHANNEL
from novatrade.bootstrap.process_events import process_next_published_event
from novatrade.domain.order import Order


class SpyConfirmationSender:
    def __init__(self) -> None:
        self.sent_order_id: UUID | None = None
        self.sent_placed_at: datetime | None = None

    def send(
        self,
        order_id: UUID,
        placed_at: datetime,
    ) -> None:
        self.sent_order_id = order_id
        self.sent_placed_at = placed_at


class SpyFulfillmentNotifier:
    def __init__(self) -> None:
        self.notified_order_id: UUID | None = None
        self.notified_placed_at: datetime | None = None

    def notify(
        self,
        order_id: UUID,
        placed_at: datetime,
    ) -> None:
        self.notified_order_id = order_id
        self.notified_placed_at = placed_at


@pytest.mark.django_db
def test_placed_order_is_processed_by_processing_application() -> None:
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

    confirmation_sender = SpyConfirmationSender()
    fulfillment_notifier = SpyFulfillmentNotifier()

    process_next_published_event(
        redis=redis,
        confirmation_sender=confirmation_sender,
        fulfillment_notifier=fulfillment_notifier,
    )

    assert response.status_code == status.HTTP_200_OK
    assert confirmation_sender.sent_order_id == order.id
    assert fulfillment_notifier.notified_order_id == order.id
