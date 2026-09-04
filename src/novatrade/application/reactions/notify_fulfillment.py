from novatrade.application.ports.fulfillment_notifier import FulfillmentNotifier
from novatrade.domain.events import OrderPlaced


def notify_fulfillment(
    event: OrderPlaced,
    notifier: FulfillmentNotifier,
) -> None:
    """Notify fulfillment about a placed Order."""
    notifier.notify(
        order_id=event.order_id,
        placed_at=event.placed_at,
    )
