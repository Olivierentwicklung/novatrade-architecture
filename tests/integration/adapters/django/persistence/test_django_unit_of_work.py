import pytest
from novatrade.adapters.django.persistence.unit_of_work import DjangoUnitOfWork

from novatrade.adapters.django.persistence.repository import DjangoOrderRepository
from novatrade.domain.order import Order


@pytest.mark.django_db(transaction=True)
def test_failed_unit_of_work_does_not_preserve_changes() -> None:
    orders = DjangoOrderRepository()

    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=1,
    )
    orders.remember(order)

    try:
        with DjangoUnitOfWork() as work:
            changed_order = work.orders.get(order.id)
            changed_order.add_product(
                product_id="BOOK-456",
                quantity=1,
            )
            work.orders.remember(changed_order)

            raise RuntimeError("Something failed")
    except RuntimeError:
        pass

    persisted_order = orders.get(order.id)

    assert persisted_order.quantity_for("BOOK-123") == 1
    assert persisted_order.quantity_for("BOOK-456") is None
