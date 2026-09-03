from uuid import UUID

from novatrade.domain.order import Order


class InMemoryOrderRepository:
    """Stores Orders in memory by identity."""

    def __init__(self) -> None:
        """Create an empty in-memory Order repository."""
        self._orders: dict[UUID, Order] = {}

    def remember(self, order: Order) -> None:
        """Remember an Order."""
        self._orders[order.id] = self._reconstitute(order)

    def get(self, order_id: UUID) -> Order:
        """Return the Order with the given identity."""
        return self._reconstitute(self._orders[order_id])

    @staticmethod
    def _reconstitute(order: Order) -> Order:
        return Order.reconstitute(
            order_id=order.id,
            status=order.status,
            placed_at=order.placed_at,
            lines=order.lines,
        )
