from uuid import UUID

from novatrade.domain.order import Order

from .models import OrderLineRecord, OrderRecord


class DjangoOrderRepository:
    """Persists Orders using Django."""

    def remember(self, order: Order) -> None:
        """Preserve an Order."""
        order_record, _ = OrderRecord.objects.update_or_create(
            id=order.id,
            defaults={
                "status": order.status.value,
            },
        )

        order_record.lines.all().delete()

        OrderLineRecord.objects.bulk_create(
            [
                OrderLineRecord(
                    order=order_record,
                    product_id=line.product_id,
                    quantity=line.quantity.value,
                )
                for line in order.lines
            ]
        )

    def get(self, order_id: UUID) -> Order:
        """Return the Order with the given identity."""
        order_record = OrderRecord.objects.get(id=order_id)

        order = Order(order_id=order_record.id)

        for line_record in order_record.lines.all():
            order.add_product(
                product_id=line_record.product_id,
                quantity=line_record.quantity,
            )

        if order_record.status == "placed":
            order.place()

        return order
