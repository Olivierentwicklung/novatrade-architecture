from novatrade.adapters.in_memory.order_repository import InMemoryOrderRepository
from novatrade.domain.order import Order


def test_remembered_order_can_be_retrieved_by_identity() -> None:
    orders = InMemoryOrderRepository()
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )

    orders.remember(order)

    retrieved_order = orders.get(order.id)

    assert retrieved_order == order


def test_changes_are_not_preserved_until_order_is_remembered_again() -> None:
    repository = InMemoryOrderRepository()
    order = Order()
    repository.remember(order)

    order.add_product(
        product_id="BOOK-123",
        quantity=1,
    )

    retrieved_order = repository.get(order.id)

    assert retrieved_order.quantity_for("BOOK-123") is None


def test_changes_to_retrieved_order_are_not_preserved_without_remembering() -> None:
    repository = InMemoryOrderRepository()
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=1,
    )
    repository.remember(order)

    retrieved_order = repository.get(order.id)

    retrieved_order.add_product(
        product_id="BOOK-456",
        quantity=1,
    )

    retrieved_again = repository.get(order.id)

    assert retrieved_again.quantity_for("BOOK-123") == 1
    assert retrieved_again.quantity_for("BOOK-456") is None
