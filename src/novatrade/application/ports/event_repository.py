from typing import Protocol

from novatrade.domain.events import OrderPlaced


class EventRepository(Protocol):
    """Preserves Domain Events that must survive the business operation."""

    def remember(self, event: OrderPlaced) -> None:
        """Preserve a Domain Event."""
        ...
