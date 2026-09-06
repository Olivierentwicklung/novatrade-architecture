import sys
from datetime import datetime
from uuid import UUID

from redis import Redis

from novatrade.adapters.redis.event_publisher import RedisEventPublisher
from novatrade.domain.events import OrderPlaced

redis = Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
)

publisher = RedisEventPublisher(redis)

event = OrderPlaced(
    order_id=UUID(sys.argv[1]),
    placed_at=datetime.fromisoformat(sys.argv[2]),
)

publisher.publish(event)
