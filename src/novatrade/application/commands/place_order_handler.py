from novatrade.application.commands.place_order import PlaceOrderCommand
from novatrade.application.place_order_and_publish import (
    place_order_and_publish,
)
from novatrade.application.ports.event_publisher import EventPublisher
from novatrade.application.ports.unit_of_work import UnitOfWork


class PlaceOrderCommandHandler:
    """Handles the intention to place an Order."""

    def __init__(
        self,
        work: UnitOfWork,
        publisher: EventPublisher,
    ) -> None:
        self._work = work
        self._publisher = publisher

    def handle(self, command: PlaceOrderCommand) -> None:
        """Execute the place Order command."""
        place_order_and_publish(
            order_id=command.order_id,
            work=self._work,
            placed_at=command.placed_at,
            publisher=self._publisher,
        )
