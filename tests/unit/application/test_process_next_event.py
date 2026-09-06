from datetime import datetime, timezone
from uuid import uuid4

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


class SpyEventDispatcher:
    def __init__(self) -> None:
        self.dispatched_event: OrderPlaced | None = None

    def dispatch(self, event: OrderPlaced) -> None:
        self.dispatched_event = event


def test_received_event_is_dispatched_to_interested_reactions() -> None:
    event = OrderPlaced(
        order_id=uuid4(),
        placed_at=PLACED_AT,
    )
    receiver = StubEventReceiver(event)
    dispatcher = SpyEventDispatcher()

    process_next_event(
        receiver=receiver,
        dispatcher=dispatcher,
    )

    assert dispatcher.dispatched_event == event
