from datetime import datetime, timezone
from uuid import UUID, uuid4

from novatrade.application.queries.order_placement_history_handler import (
    OrderPlacementHistoryQueryHandler,
)

from novatrade.application.queries.order_placement_history import (
    OrderPlacementHistoryQuery,
)

PLACED_AT = datetime(
    2026,
    9,
    6,
    10,
    30,
    tzinfo=timezone.utc,
)


class StubOrderPlacementHistory:
    def __init__(
        self,
        entries: tuple[tuple[UUID, datetime], ...],
    ) -> None:
        self._entries = entries

    def list(self) -> tuple[tuple[UUID, datetime], ...]:
        return self._entries


def test_order_placement_history_query_is_handled() -> None:
    order_id = uuid4()
    history = StubOrderPlacementHistory(
        entries=((order_id, PLACED_AT),),
    )
    handler = OrderPlacementHistoryQueryHandler(history=history)
    query = OrderPlacementHistoryQuery()

    entries = handler.handle(query)

    assert entries == ((order_id, PLACED_AT),)
