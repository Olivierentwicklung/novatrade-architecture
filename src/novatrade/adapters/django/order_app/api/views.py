from datetime import datetime, timezone
from uuid import UUID

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from novatrade.adapters.django.order_app.persistence.unit_of_work import (
    DjangoUnitOfWork,
)
from novatrade.application.use_cases.place_order import place_order


class PlaceOrderView(APIView):
    """HTTP entry point for placing an Order."""

    def post(self, request: Request, order_id: UUID) -> Response:
        place_order(
            order_id=order_id,
            work=DjangoUnitOfWork(),
            placed_at=datetime.now(timezone.utc),
        )

        return Response(status=200)
