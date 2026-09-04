from datetime import datetime, timezone

import pytest

from novatrade.adapters.django.persistence.models import OrderPlacedRecord
from novatrade.adapters.django.persistence.repository import DjangoOrderRepository
from novatrade.adapters.django.persistence.unit_of_work import DjangoUnitOfWork
from novatrade.domain.order import Order, OrderStatus

PLACED_AT = datetime(
    2026,
    9,
    4,
    11,
    0,
    tzinfo=timezone.utc,
)


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


@pytest.mark.django_db(transaction=True)
def test_successful_unit_of_work_preserves_changes() -> None:
    orders = DjangoOrderRepository()

    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=1,
    )
    orders.remember(order)

    with DjangoUnitOfWork() as work:
        changed_order = work.orders.get(order.id)
        changed_order.add_product(
            product_id="BOOK-456",
            quantity=1,
        )
        work.orders.remember(changed_order)

    persisted_order = orders.get(order.id)

    assert persisted_order.quantity_for("BOOK-123") == 1
    assert persisted_order.quantity_for("BOOK-456") == 1


@pytest.mark.django_db(transaction=True)
def test_successful_unit_of_work_preserves_order_placed_fact() -> None:
    orders = DjangoOrderRepository()

    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=1,
    )
    orders.remember(order)

    with DjangoUnitOfWork() as work:
        changed_order = work.orders.get(order.id)
        changed_order.place(PLACED_AT)
        work.orders.remember(changed_order)

        for event in changed_order.collect_events():
            work.events.remember(event)

    persisted_event = OrderPlacedRecord.objects.get(
        order_id=order.id,
    )

    assert persisted_event.placed_at == PLACED_AT


@pytest.mark.django_db(transaction=True)
def test_failed_unit_of_work_rolls_back_order_and_placed_fact() -> None:
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
            changed_order.place(PLACED_AT)
            work.orders.remember(changed_order)

            for event in changed_order.collect_events():
                work.events.remember(event)

            raise RuntimeError("Something failed")
    except RuntimeError:
        pass

    persisted_order = orders.get(order.id)

    assert persisted_order.status is OrderStatus.DRAFT
    assert not OrderPlacedRecord.objects.filter(
        order_id=order.id,
    ).exists()
