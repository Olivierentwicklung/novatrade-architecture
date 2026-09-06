from datetime import datetime, timezone
from uuid import UUID, uuid4

from novatrade.application.event_dispatcher_factory import (
    build_event_dispatcher,
)

from novatrade.domain.events import OrderPlaced

PLACED_AT = datetime(
    2026,
    9,
    6,
    10,
    30,
    tzinfo=timezone.utc,
)


class SpyConfirmationSender:
    def __init__(self) -> None:
        self.sent_order_id: UUID | None = None

    def send(
        self,
        order_id: UUID,
        placed_at: datetime,
    ) -> None:
        self.sent_order_id = order_id


class SpyFulfillmentNotifier:
    def __init__(self) -> None:
        self.notified_order_id: UUID | None = None

    def notify(
        self,
        order_id: UUID,
        placed_at: datetime,
    ) -> None:
        self.notified_order_id = order_id


def test_order_placed_is_connected_to_its_reactions() -> None:
    sender = SpyConfirmationSender()
    notifier = SpyFulfillmentNotifier()

    dispatcher = build_event_dispatcher(
        confirmation_sender=sender,
        fulfillment_notifier=notifier,
    )

    event = OrderPlaced(
        order_id=uuid4(),
        placed_at=PLACED_AT,
    )

    dispatcher.dispatch(event)

    assert sender.sent_order_id == event.order_id
    assert notifier.notified_order_id == event.order_id
