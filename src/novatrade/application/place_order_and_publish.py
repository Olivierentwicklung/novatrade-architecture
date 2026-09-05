from datetime import datetime
from uuid import UUID

from novatrade.application.ports.event_publisher import EventPublisher
from novatrade.application.ports.unit_of_work import UnitOfWork
from novatrade.application.use_cases.place_order import place_order


def place_order_and_publish(
    order_id: UUID,
    work: UnitOfWork,
    placed_at: datetime,
    publisher: EventPublisher,
) -> None:
    """Place an Order and publish the Domain Events it produces."""
    events = place_order(
        order_id=order_id,
        work=work,
        placed_at=placed_at,
    )

    for event in events:
        publisher.publish(event)
