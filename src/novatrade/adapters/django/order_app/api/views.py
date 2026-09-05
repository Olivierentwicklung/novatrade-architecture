from uuid import UUID

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class PlaceOrderView(APIView):
    """HTTP entry point for placing an Order."""

    def post(self, request: Request, order_id: UUID) -> Response:
        return Response(status=200)
