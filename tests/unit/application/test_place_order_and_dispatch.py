from datetime import datetime, timezone

from novatrade.application.place_order_and_dispatch import place_order_and_dispatch

PLACED_AT = datetime(
    2026,
    9,
    4,
    10,
    30,
    tzinfo=timezone.utc,
)


def test_successfully_placed_order_dispatches_its_domain_events() -> None:
    place_order_and_dispatch()
