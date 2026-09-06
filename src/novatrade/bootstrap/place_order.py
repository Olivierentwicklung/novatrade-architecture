from redis import Redis

from novatrade.adapters.django.order_app.persistence.unit_of_work import (
    DjangoUnitOfWork,
)
from novatrade.adapters.redis.event_publisher import RedisEventPublisher
from novatrade.application.commands.place_order_handler import (
    PlaceOrderCommandHandler,
)


def place_order_handler_factory(
    redis: Redis | None = None,
) -> PlaceOrderCommandHandler:
    """Assemble the production handler for placing Orders."""
    redis_client = redis or Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
    )

    return PlaceOrderCommandHandler(
        work=DjangoUnitOfWork(),
        publisher=RedisEventPublisher(redis_client),
    )
