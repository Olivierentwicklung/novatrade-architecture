from datetime import datetime
from uuid import UUID

from novatrade.adapters.django.order_app.models import OrderPlacedRecord


class DjangoOrderPlacementHistory:
    """Reads recorded Order placement history using Django."""

    def list(self) -> tuple[tuple[UUID, datetime], ...]:
        """Return recorded Order placements."""
        return tuple(
            OrderPlacedRecord.objects.values_list(
                "order_id",
                "placed_at",
            )
        )
