from datetime import datetime, timezone
from uuid import UUID

from flask import Blueprint

from novatrade.application.commands.place_order import PlaceOrderCommand
from novatrade.application.commands.place_order_handler import (
    PlaceOrderCommandHandler,
)


def create_order_blueprint(
    place_order_handler: PlaceOrderCommandHandler,
) -> Blueprint:
    """Create the Flask routes for Order operations."""
    orders = Blueprint("orders", __name__)

    @orders.post("/orders/<uuid:order_id>/place")
    def place_order(order_id: UUID) -> tuple[str, int]:
        command = PlaceOrderCommand(
            order_id=order_id,
            placed_at=datetime.now(timezone.utc),
        )

        place_order_handler.handle(command)

        return "", 200

    return orders
