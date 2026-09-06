from datetime import datetime
from uuid import UUID

from novatrade.application.ports.order_placement_history import (
    OrderPlacementHistory,
)


def list_order_placement_history(
    history: OrderPlacementHistory,
) -> tuple[tuple[UUID, datetime], ...]:
    """Return recorded Order placement history."""
    return history.list()
