from types import TracebackType

from django.db import transaction

from novatrade.adapters.django.persistence.repository import DjangoOrderRepository


class DjangoUnitOfWork:
    """Provides transactional persistence for one application operation."""

    def __init__(self) -> None:
        self._transaction = None
        self.orders = DjangoOrderRepository()

    def __enter__(self) -> "DjangoUnitOfWork":
        self._transaction = transaction.atomic()
        self._transaction.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool | None:
        if self._transaction is None:
            return None

        return self._transaction.__exit__(
            exc_type,
            exc_value,
            traceback,
        )

    def commit(self) -> None:
        pass
