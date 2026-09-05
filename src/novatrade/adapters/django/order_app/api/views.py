from datetime import datetime, timezone
from uuid import UUID

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from novatrade.adapters.django.order_app.persistence.unit_of_work import (
    DjangoUnitOfWork,
)
from novatrade.application.ports.order_repository_errors import OrderNotFound
from novatrade.application.use_cases.place_order import place_order
from novatrade.domain.order import CannotPlaceEmptyOrder


class PlaceOrderView(APIView):
    """HTTP entry point for placing an Order."""

    def post(self, request: Request, order_id: UUID) -> Response:
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
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
