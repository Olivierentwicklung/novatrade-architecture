from typing import Protocol

from novatrade.domain.events import OrderPlaced


class EventReceiver(Protocol):
    """Receives Domain Events waiting to be processed."""

    def receive(self) -> OrderPlaced | None:
        """Receive the next Domain Event waiting to be processed."""
        ...
