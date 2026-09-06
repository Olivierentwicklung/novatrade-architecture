from datetime import datetime
from uuid import UUID

from novatrade.application.list_order_placement_history import (
    list_order_placement_history,
)
from novatrade.application.ports.order_placement_history import (
    OrderPlacementHistory,
)
from novatrade.application.queries.order_placement_history import (
    OrderPlacementHistoryQuery,
)


class OrderPlacementHistoryQueryHandler:
    """Handles requests for recorded Order placement history."""

    def __init__(
        self,
        history: OrderPlacementHistory,
    ) -> None:
        self._history = history

    def handle(
        self,
        query: OrderPlacementHistoryQuery,
    ) -> tuple[tuple[UUID, datetime], ...]:
        """Execute the Order placement history query."""
        return list_order_placement_history(self._history)
