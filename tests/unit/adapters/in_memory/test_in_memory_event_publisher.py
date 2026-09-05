from datetime import datetime, timezone
from uuid import uuid4

from novatrade.adapters.in_memory.event_publisher import InMemoryEventPublisher

from novatrade.domain.events import OrderPlaced

PLACED_AT = datetime(
    2026,
    9,
    4,
    10,
    30,
    tzinfo=timezone.utc,
)


def test_published_event_is_available_for_later_processing() -> None:
    publisher = InMemoryEventPublisher()

    event = OrderPlaced(
        order_id=uuid4(),
        placed_at=PLACED_AT,
    )

    publisher.publish(event)

    assert publisher.pending_events == (event,)
