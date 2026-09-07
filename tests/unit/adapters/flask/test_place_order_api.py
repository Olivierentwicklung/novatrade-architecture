from uuid import uuid4

from novatrade.adapters.flask.app import create_app

from novatrade.application.commands.place_order import PlaceOrderCommand


class SpyPlaceOrderCommandHandler:
    """Records the command passed through the Flask adapter."""

    def __init__(self) -> None:
        self.handled_command: PlaceOrderCommand | None = None

    def handle(self, command: PlaceOrderCommand) -> None:
        self.handled_command = command


def test_post_place_order_translates_http_request_to_command() -> None:
    handler = SpyPlaceOrderCommandHandler()
    app = create_app(place_order_handler=handler)
    client = app.test_client()
    order_id = uuid4()

    response = client.post(f"/orders/{order_id}/place")

    assert response.status_code == 200

    command = handler.handled_command

    assert command is not None
    assert command.order_id == order_id
    assert command.placed_at.tzinfo is not None
