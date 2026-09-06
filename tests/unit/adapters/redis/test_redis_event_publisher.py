from datetime import datetime, timezone
from uuid import uuid4

import fakeredis

from novatrade.adapters.redis.event_publisher import RedisEventPublisher
from novatrade.domain.events import OrderPlaced

PLACED_AT = datetime(
    2026,
    9,
    6,
    10,
    30,
    tzinfo=timezone.utc,
)


def test_published_event_is_stored_outside_the_publisher() -> None:
    redis = fakeredis.FakeRedis(decode_responses=True)
    publisher = RedisEventPublisher(redis)

    event = OrderPlaced(
        order_id=uuid4(),
        placed_at=PLACED_AT,
    )

    publisher.publish(event)

    assert redis.llen("novatrade:events") == 1
