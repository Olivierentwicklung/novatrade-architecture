from types import TracebackType
from typing import Protocol

from novatrade.application.ports.event_repository import EventRepository
from novatrade.application.ports.order_repository import OrderRepository


class UnitOfWork(Protocol):
    """Provides persistence resources for one application operation."""

    @property
    def orders(self) -> OrderRepository:
        """Provide access to Orders participating in this operation."""
        ...

    def __enter__(self) -> "UnitOfWork":
        """Begin the persistence boundary for the operation."""
        ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        """End the persistence boundary for the operation."""
        ...

    @property
    def events(self) -> EventRepository:
        """Provide access to Domain Events participating in this operation."""
        ...
