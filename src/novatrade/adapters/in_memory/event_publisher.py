from novatrade.domain.events import OrderPlaced


class InMemoryEventPublisher:
    """Holds published Domain Events for later processing."""

    def __init__(self) -> None:
        self._pending_events: list[OrderPlaced] = []

    @property
    def pending_events(self) -> tuple[OrderPlaced, ...]:
        """Return Domain Events waiting to be processed."""
        return tuple(self._pending_events)

    def publish(self, event: OrderPlaced) -> None:
        """Publish a Domain Event for later processing."""
        self._pending_events.append(event)
