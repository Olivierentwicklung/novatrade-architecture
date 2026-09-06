from datetime import datetime, timezone
from uuid import UUID, uuid4

from novatrade.application.event_dispatcher_factory import (
    build_event_dispatcher,
)
from novatrade.application.process_next_event import process_next_event
from novatrade.domain.events import OrderPlaced

PLACED_AT = datetime(
    2026,
    9,
    6,
    10,
    30,
    tzinfo=timezone.utc,
)


class StubEventReceiver:
    def __init__(self, event: OrderPlaced) -> None:
        self._event = event

    def receive(self) -> OrderPlaced:
        return self._event


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


def test_received_order_placed_triggers_its_application_reactions() -> None:
    event = OrderPlaced(
        order_id=uuid4(),
        placed_at=PLACED_AT,
    )
    receiver = StubEventReceiver(event)
    confirmation_sender = SpyConfirmationSender()
    fulfillment_notifier = SpyFulfillmentNotifier()

    dispatcher = build_event_dispatcher(
        confirmation_sender=confirmation_sender,
        fulfillment_notifier=fulfillment_notifier,
    )

    process_next_event(
        receiver=receiver,
        dispatcher=dispatcher,
    )

    assert confirmation_sender.sent_order_id == event.order_id
    assert confirmation_sender.sent_placed_at == event.placed_at
    assert fulfillment_notifier.notified_order_id == event.order_id
    assert fulfillment_notifier.notified_placed_at == event.placed_at
