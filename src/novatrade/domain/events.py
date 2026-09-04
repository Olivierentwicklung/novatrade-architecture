from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class OrderPlaced:
    """Records the fact that an Order was successfully placed."""

    order_id: UUID
    placed_at: datetime
