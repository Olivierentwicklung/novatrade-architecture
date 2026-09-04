from datetime import datetime, timezone
from uuid import uuid4

from novatrade.application.event_dispatcher import EventDispatcher

from novatrade.domain.events import OrderPlaced

PLACED_AT = datetime(
    2026,
    9,
    4,
    10,
    30,
    tzinfo=timezone.utc,
)


def test_dispatches_event_to_all_interested_reactions() -> None:
    received_by_first: list[OrderPlaced] = []
    received_by_second: list[OrderPlaced] = []

    def first_reaction(event: OrderPlaced) -> None:
        received_by_first.append(event)

    def second_reaction(event: OrderPlaced) -> None:
        received_by_second.append(event)

    dispatcher = EventDispatcher(
        reactions={
            OrderPlaced: (
                first_reaction,
                second_reaction,
            ),
        }
    )

    event = OrderPlaced(
        order_id=uuid4(),
        placed_at=PLACED_AT,
    )

    dispatcher.dispatch(event)

    assert received_by_first == [event]
    assert received_by_second == [event]
