from datetime import datetime, timezone
from uuid import uuid4

import pytest
from novatrade.adapters.django.order_app.persistence.order_placement_history import (
    DjangoOrderPlacementHistory,
)

from novatrade.adapters.django.order_app.models import OrderPlacedRecord

FIRST_PLACED_AT = datetime(
    2026,
    9,
    5,
    10,
    30,
    tzinfo=timezone.utc,
)

SECOND_PLACED_AT = datetime(
    2026,
    9,
    6,
    11,
    45,
    tzinfo=timezone.utc,
)


@pytest.mark.django_db
def test_recorded_order_placements_can_be_retrieved() -> None:
    first_order_id = uuid4()
    second_order_id = uuid4()

    OrderPlacedRecord.objects.create(
        order_id=first_order_id,
        placed_at=FIRST_PLACED_AT,
    )
    OrderPlacedRecord.objects.create(
        order_id=second_order_id,
        placed_at=SECOND_PLACED_AT,
    )

    history = DjangoOrderPlacementHistory()

    entries = history.list()

    assert set(entries) == {
        (first_order_id, FIRST_PLACED_AT),
        (second_order_id, SECOND_PLACED_AT),
    }
