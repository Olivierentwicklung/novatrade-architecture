from uuid import UUID

from novatrade.domain.order import Order


class InMemoryOrderRepository:
    """Stores Orders in memory by identity."""

    def __init__(self) -> None:
        """Create an empty in-memory Order repository."""
        self._orders: dict[UUID, Order] = {}

    def remember(self, order: Order) -> None:
        """Remember an Order."""
        self._orders[order.id] = order

    def get(self, order_id: UUID) -> Order:
        """Return the Order with the given identity."""
        return self._orders[order_id]
