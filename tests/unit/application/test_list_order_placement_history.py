from datetime import datetime, timezone
from uuid import UUID, uuid4

from novatrade.application.list_order_placement_history import (
    list_order_placement_history,
)

PLACED_AT = datetime(2026, 9, 6, 10, 30, tzinfo=timezone.utc)


class StubOrderPlacementHistory:
    def __init__(
        self,
        entries: tuple[tuple[UUID, datetime], ...],
    ) -> None:
        self._entries = entries

    def list(self) -> tuple[tuple[UUID, datetime], ...]:
        return self._entries


def test_recorded_order_placement_history_can_be_retrieved() -> None:
    order_id = uuid4()
    history = StubOrderPlacementHistory(
        entries=((order_id, PLACED_AT),),
    )

    entries = list_order_placement_history(history)

    assert entries == ((order_id, PLACED_AT),)
