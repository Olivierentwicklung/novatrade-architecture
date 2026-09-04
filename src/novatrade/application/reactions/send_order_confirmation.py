from novatrade.application.ports.order_confirmation_sender import (
    OrderConfirmationSender,
)
from novatrade.domain.events import OrderPlaced


def send_order_confirmation(
    event: OrderPlaced,
    sender: OrderConfirmationSender,
) -> None:
    """Send a customer confirmation for a placed Order."""
    sender.send(
        order_id=event.order_id,
        placed_at=event.placed_at,
    )
