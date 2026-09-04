from datetime import datetime
from typing import Protocol
from uuid import UUID


class OrderConfirmationSender(Protocol):
    """Sends a confirmation for a successfully placed Order."""

    def send(
        self,
        order_id: UUID,
        placed_at: datetime,
    ) -> None:
        """Send confirmation for the placed Order."""
        ...
