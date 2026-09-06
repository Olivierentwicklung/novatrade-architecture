from redis import Redis

from novatrade.adapters.redis.event_receiver import RedisEventReceiver

redis = Redis(
    host="localhost",
    port=6379,
    decode_responses=True,
)

receiver = RedisEventReceiver(redis)

event = receiver.receive()

if event is None:
    raise RuntimeError("Expected a Domain Event.")

print(f"{event.order_id}|{event.placed_at.isoformat()}")
