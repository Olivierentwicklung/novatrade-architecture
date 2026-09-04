from datetime import datetime, timezone
from uuid import UUID, uuid4

from novatrade.application.send_order_confirmation import send_order_confirmation
from novatrade.domain.events import OrderPlaced

PLACED_AT = datetime(
    2026,
    9,
    4,
    10,
    30,
    tzinfo=timezone.utc,
)


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


def test_order_placed_sends_customer_confirmation() -> None:
    event = OrderPlaced(
        order_id=uuid4(),
        placed_at=PLACED_AT,
    )
    sender = SpyConfirmationSender()

    send_order_confirmation(
        event=event,
        sender=sender,
    )

    assert sender.sent_order_id == event.order_id
    assert sender.sent_placed_at == event.placed_at
