import json

from redis import Redis

from novatrade.domain.events import OrderPlaced


class RedisEventPublisher:
    """Publishes Domain Events to Redis."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    def publish(self, event: OrderPlaced) -> None:
        """Publish a Domain Event for later processing."""
        payload = json.dumps(
            {
                "type": "OrderPlaced",
                "order_id": str(event.order_id),
                "placed_at": event.placed_at.isoformat(),
            }
        )

        self._redis.rpush("novatrade:events", payload)
