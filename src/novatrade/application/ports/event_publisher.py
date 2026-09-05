from typing import Protocol

from novatrade.domain.events import OrderPlaced


class EventPublisher(Protocol):
    """Publishes Domain Events for processing outside the current execution."""

    def publish(self, event: OrderPlaced) -> None:
        """Publish a Domain Event for later processing."""
        ...
