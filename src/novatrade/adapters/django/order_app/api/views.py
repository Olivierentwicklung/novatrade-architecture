from datetime import datetime, timezone
from uuid import UUID

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from novatrade.adapters.django.order_app.persistence.order_repository import (
    DjangoOrderRepository,
)
from novatrade.adapters.django.order_app.persistence.unit_of_work import (
    DjangoUnitOfWork,
)
from novatrade.application.ports.order_repository_errors import OrderNotFound
from novatrade.application.use_cases.get_order import get_order
from novatrade.application.use_cases.list_orders import list_orders
from novatrade.application.use_cases.place_order import place_order
from novatrade.domain.order import CannotPlaceEmptyOrder


class PlaceOrderView(APIView):
    """HTTP entry point for placing an Order."""

    def post(self, request: Request, order_id: UUID) -> Response:
        """Place the requested Order and translate failures to HTTP responses."""
        try:
            place_order(
                order_id=order_id,
                work=DjangoUnitOfWork(),
                placed_at=datetime.now(timezone.utc),
            )
        except OrderNotFound:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except CannotPlaceEmptyOrder:
            return Response(status=status.HTTP_409_CONFLICT)

        return Response(status=status.HTTP_200_OK)


class OrderDetailView(APIView):
    """HTTP entry point for retrieving an Order."""

    def get(self, request: Request, order_id: UUID) -> Response:
        """Return the requested Order as an HTTP representation."""
        try:
            order = get_order(
                order_id=order_id,
                orders=DjangoOrderRepository(),
            )
        except OrderNotFound:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "id": str(order.id),
                "status": order.status.value,
            },
            status=status.HTTP_200_OK,
        )


class OrderListView(APIView):
    """HTTP entry point for retrieving Orders."""

    def get(self, request: Request) -> Response:
        """Return the Orders as HTTP representations."""
        orders = list_orders(
            orders=DjangoOrderRepository(),
        )

        return Response(
            [
                {
                    "id": str(order.id),
                    "status": order.status.value,
                }
                for order in orders
            ],
            status=status.HTTP_200_OK,
        )
