from collections.abc import Callable
from typing import TypeAlias

from novatrade.domain.events import OrderPlaced

Reaction: TypeAlias = Callable[[OrderPlaced], None]


class EventDispatcher:
    """Dispatches Domain Events to their interested reactions."""

    def __init__(
        self,
        reactions: dict[type[OrderPlaced], tuple[Reaction, ...]],
    ) -> None:
        self._reactions = reactions

    def dispatch(self, event: OrderPlaced) -> None:
        """Dispatch an event to all interested reactions."""
        for reaction in self._reactions.get(type(event), ()):
            reaction(event)
