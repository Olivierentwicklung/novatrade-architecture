from datetime import datetime
from typing import Protocol
from uuid import UUID


class OrderPlacementHistory(Protocol):
    """Provides recorded Order placement history."""

    def list(self) -> tuple[tuple[UUID, datetime], ...]:
        """Return recorded Order placements."""
        ...
