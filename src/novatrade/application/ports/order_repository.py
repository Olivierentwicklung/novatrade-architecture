from typing import Protocol
from uuid import UUID

from novatrade.domain.order import Order


class OrderRepository(Protocol):
    """Provides access to and preserves Orders."""

    def get(self, order_id: UUID) -> Order:
        """Return the Order with the given identity."""
        ...

    def list(self) -> tuple[Order, ...]:
        """Return the preserved Orders."""
        ...

    def remember(self, order: Order) -> None:
        """Preserve an Order."""
        ...
