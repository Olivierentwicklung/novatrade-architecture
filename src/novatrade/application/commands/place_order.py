from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class PlaceOrderCommand:
    """Represents the intention to place an Order."""

    order_id: UUID
    placed_at: datetime
