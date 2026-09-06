import json
from datetime import datetime
from uuid import UUID

from redis import Redis

from novatrade.domain.events import OrderPlaced


class RedisEventReceiver:
    """Receives Domain Events from Redis."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    def receive(self) -> OrderPlaced | None:
        """Receive the next Domain Event waiting to be processed."""
        payload = self._redis.lpop("novatrade:events")

        if payload is None:
            return None

        if isinstance(payload, list):
            raise TypeError("Expected a single Redis event payload.")

        data = json.loads(payload)

        return OrderPlaced(
            order_id=UUID(data["order_id"]),
            placed_at=datetime.fromisoformat(data["placed_at"]),
        )
