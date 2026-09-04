from datetime import datetime, timezone
from uuid import UUID, uuid4

from novatrade.application.reactions.notify_fulfillment import notify_fulfillment
from novatrade.domain.events import OrderPlaced

PLACED_AT = datetime(
    2026,
    9,
    4,
    10,
    30,
    tzinfo=timezone.utc,
)


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


def test_order_placed_notifies_fulfillment() -> None:
    event = OrderPlaced(
        order_id=uuid4(),
        placed_at=PLACED_AT,
    )
    notifier = SpyFulfillmentNotifier()

    notify_fulfillment(
        event=event,
        notifier=notifier,
    )

    assert notifier.notified_order_id == event.order_id
    assert notifier.notified_placed_at == event.placed_at
