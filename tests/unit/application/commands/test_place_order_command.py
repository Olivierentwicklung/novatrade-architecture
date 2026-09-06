from datetime import datetime, timezone
from uuid import uuid4

from novatrade.application.commands.place_order import PlaceOrderCommand

PLACED_AT = datetime(
    2026,
    9,
    6,
    18,
    30,
    tzinfo=timezone.utc,
)


def test_place_order_command_represents_the_intention_to_place_an_order() -> None:
    order_id = uuid4()

    command = PlaceOrderCommand(
        order_id=order_id,
        placed_at=PLACED_AT,
    )

    assert command.order_id == order_id
    assert command.placed_at == PLACED_AT
