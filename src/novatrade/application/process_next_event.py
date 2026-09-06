from novatrade.application.event_dispatcher import EventDispatcher
from novatrade.application.ports.event_receiver import EventReceiver


def process_next_event(
    receiver: EventReceiver,
    dispatcher: EventDispatcher,
) -> None:
    """Receive and dispatch the next available Domain Event."""
    event = receiver.receive()

    if event is not None:
        dispatcher.dispatch(event)
