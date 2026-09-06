from dataclasses import dataclass


@dataclass(frozen=True)
class OrderPlacementHistoryQuery:
    """Represents a request for recorded Order placement history."""
