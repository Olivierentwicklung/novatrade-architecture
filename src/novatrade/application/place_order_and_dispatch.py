from datetime import datetime
from uuid import UUID

from novatrade.application.event_dispatcher import EventDispatcher
from novatrade.application.ports.unit_of_work import UnitOfWork
from novatrade.application.use_cases.place_order import place_order


def place_order_and_dispatch(
    order_id: UUID,
    work: UnitOfWork,
    placed_at: datetime,
    dispatcher: EventDispatcher,
) -> None:
    """Place an Order and dispatch the Domain Events it produces."""
    events = place_order(
        order_id=order_id,
        work=work,
        placed_at=placed_at,
    )

    for event in events:
        dispatcher.dispatch(event)
