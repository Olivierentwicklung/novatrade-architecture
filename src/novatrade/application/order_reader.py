from typing import Protocol
from uuid import UUID

from novatrade.domain.order import Order


class OrderReader(Protocol):
    """Provides access to Orders by identity."""

    def get(self, order_id: UUID) -> Order:
        """Return the Order with the given identity."""
        ...
