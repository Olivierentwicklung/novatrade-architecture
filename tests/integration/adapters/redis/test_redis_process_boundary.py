import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from redis import Redis

from novatrade.adapters.redis.event_channel import EVENT_CHANNEL
from novatrade.domain.events import OrderPlaced

PLACED_AT = datetime(
    2026,
    9,
    6,
    10,
    30,
    tzinfo=timezone.utc,
)

PROJECT_ROOT = Path(__file__).resolve().parents[4]


def test_event_published_by_one_process_is_received_by_another() -> None:
    redis = Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
    )
    redis.delete(EVENT_CHANNEL)

    event = OrderPlaced(
        order_id=uuid4(),
        placed_at=PLACED_AT,
    )

    subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tests" / "support" / "publish_event.py"),
            str(event.order_id),
            event.placed_at.isoformat(),
        ],
        check=True,
    )

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tests" / "support" / "receive_event.py"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == (f"{event.order_id}|{event.placed_at.isoformat()}")
