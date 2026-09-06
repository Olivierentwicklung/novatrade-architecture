from redis import Redis

from novatrade.adapters.django.order_app.persistence.unit_of_work import (
    DjangoUnitOfWork,
)
from novatrade.adapters.redis.event_publisher import RedisEventPublisher
from novatrade.application.commands.place_order_handler import (
    PlaceOrderCommandHandler,
)


def place_order_handler_factory(
    redis: Redis,
) -> PlaceOrderCommandHandler:
    """Assemble the production handler for placing Orders."""
    return PlaceOrderCommandHandler(
        work=DjangoUnitOfWork(),
        publisher=RedisEventPublisher(redis),
    )
