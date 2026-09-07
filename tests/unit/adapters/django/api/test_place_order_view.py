from uuid import uuid4

from rest_framework.test import APIRequestFactory

from novatrade.adapters.django.order_app.api.views import PlaceOrderView
from novatrade.application.commands.place_order import PlaceOrderCommand


class SpyPlaceOrderCommandHandler:
    def __init__(self) -> None:
        self.handled_command: PlaceOrderCommand | None = None

    def handle(self, command: PlaceOrderCommand) -> None:
        self.handled_command = command


def test_place_order_request_is_delegated_as_command() -> None:
    order_id = uuid4()
    handler = SpyPlaceOrderCommandHandler()
    request = APIRequestFactory().post("/orders/place/")

    view = PlaceOrderView(handler=handler)

    view.post(
        request=request,
        order_id=order_id,
    )

    assert handler.handled_command is not None
    assert handler.handled_command.order_id == order_id
