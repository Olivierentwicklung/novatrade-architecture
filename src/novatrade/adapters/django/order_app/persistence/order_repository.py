from uuid import UUID

from novatrade.application.ports.order_repository_errors import OrderNotFound
from novatrade.domain.order import Order, OrderLine, OrderStatus
from novatrade.domain.quantity import Quantity

from ..models import OrderLineRecord, OrderRecord


class DjangoOrderRepository:
    """Persists Orders using Django."""

    def remember(self, order: Order) -> None:
        """Preserve an Order."""
        order_record, _ = OrderRecord.objects.update_or_create(
            id=order.id,
            defaults={
                "status": order.status.value,
                "created_at": order.created_at,
                "placed_at": order.placed_at,
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
        try:
            order_record = OrderRecord.objects.get(id=order_id)
        except OrderRecord.DoesNotExist as error:
            raise OrderNotFound from error

        return self._reconstitute(order_record)

    def list(self) -> tuple[Order, ...]:
        """Return the preserved Orders."""
        return tuple(
            self._reconstitute(order_record)
            for order_record in OrderRecord.objects.all()
        )

    def latest(self, limit: int) -> tuple[Order, ...]:
        """Return the most recently created Orders, newest first."""
        order_records = OrderRecord.objects.order_by("-created_at")[:limit]

        return tuple(self._reconstitute(order_record) for order_record in order_records)

    @staticmethod
    def _reconstitute(order_record: OrderRecord) -> Order:
        """Reconstitute a Domain Order from its persistence record."""
        return Order.reconstitute(
            order_id=order_record.id,
            status=OrderStatus(order_record.status),
            created_at=order_record.created_at,
            placed_at=order_record.placed_at,
            lines=tuple(
                OrderLine(
                    product_id=line_record.product_id,
                    quantity=Quantity(line_record.quantity),
                )
                for line_record in order_record.lines.all()
            ),
        )
