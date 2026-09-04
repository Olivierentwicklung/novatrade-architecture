from datetime import datetime
from typing import Protocol
from uuid import UUID


class FulfillmentNotifier(Protocol):
    """Notifies fulfillment about a successfully placed Order."""

    def notify(
        self,
        order_id: UUID,
        placed_at: datetime,
    ) -> None:
        """Notify fulfillment about the placed Order."""
        ...
