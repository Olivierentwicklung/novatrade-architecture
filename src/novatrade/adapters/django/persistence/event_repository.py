from novatrade.adapters.django.persistence.models import OrderPlacedRecord
from novatrade.domain.events import OrderPlaced


class DjangoEventRepository:
    """Persists Domain Events using Django."""

    def remember(self, event: OrderPlaced) -> None:
        """Preserve a Domain Event."""
        OrderPlacedRecord.objects.create(
            order_id=event.order_id,
            placed_at=event.placed_at,
        )
