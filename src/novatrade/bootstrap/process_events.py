from redis import Redis

from novatrade.adapters.redis.event_receiver import RedisEventReceiver
from novatrade.application.event_dispatcher_factory import (
    build_event_dispatcher,
)
from novatrade.application.ports.fulfillment_notifier import (
    FulfillmentNotifier,
)
from novatrade.application.ports.order_confirmation_sender import (
    OrderConfirmationSender,
)
from novatrade.application.process_next_event import process_next_event


def process_next_published_event(
    redis: Redis,
    confirmation_sender: OrderConfirmationSender,
    fulfillment_notifier: FulfillmentNotifier,
) -> None:
    """Process the next published Domain Event."""
    receiver = RedisEventReceiver(redis)

    dispatcher = build_event_dispatcher(
        confirmation_sender=confirmation_sender,
        fulfillment_notifier=fulfillment_notifier,
    )

    process_next_event(
        receiver=receiver,
        dispatcher=dispatcher,
    )
