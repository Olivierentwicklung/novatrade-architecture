from functools import partial

from novatrade.application.event_dispatcher import EventDispatcher
from novatrade.application.ports.fulfillment_notifier import (
    FulfillmentNotifier,
)
from novatrade.application.ports.order_confirmation_sender import (
    OrderConfirmationSender,
)
from novatrade.application.reactions.notify_fulfillment import (
    notify_fulfillment,
)
from novatrade.application.reactions.send_order_confirmation import (
    send_order_confirmation,
)
from novatrade.domain.events import OrderPlaced


def build_event_dispatcher(
    confirmation_sender: OrderConfirmationSender,
    fulfillment_notifier: FulfillmentNotifier,
) -> EventDispatcher:
    """Build the dispatcher with the reactions interested in Domain Events."""
    return EventDispatcher(
        reactions={
            OrderPlaced: (
                partial(
                    send_order_confirmation,
                    sender=confirmation_sender,
                ),
                partial(
                    notify_fulfillment,
                    notifier=fulfillment_notifier,
                ),
            ),
        }
    )
