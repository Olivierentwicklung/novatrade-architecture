from typing import Protocol

from novatrade.application.ports.order_repository import OrderRepository


class UnitOfWork(Protocol):
    """Provides persistence resources for one application operation."""

    @property
    def orders(self) -> OrderRepository:
        """Provide access to Orders participating in this operation."""
        ...

    def commit(self) -> None:
        """Commit the work performed by the application operation."""
        ...
