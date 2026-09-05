from datetime import datetime, timezone
from uuid import uuid4

import pytest

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


def test_reaction_failure_does_not_undo_already_executed_reactions() -> None:
    received_events: list[OrderPlaced] = []

    def successful_reaction(event: OrderPlaced) -> None:
        received_events.append(event)

    def failing_reaction(event: OrderPlaced) -> None:
        raise RuntimeError("fulfillment failed")

    dispatcher = EventDispatcher(
        reactions={
            OrderPlaced: (
                successful_reaction,
                failing_reaction,
            ),
        }
    )

    event = OrderPlaced(
        order_id=uuid4(),
        placed_at=PLACED_AT,
    )

    with pytest.raises(RuntimeError, match="fulfillment failed"):
        dispatcher.dispatch(event)

    assert received_events == [event]
