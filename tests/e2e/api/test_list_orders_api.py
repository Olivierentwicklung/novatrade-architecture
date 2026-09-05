from uuid import UUID

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from novatrade.adapters.django.order_app.persistence.order_repository import (
    DjangoOrderRepository,
)
from novatrade.domain.order import Order


@pytest.mark.django_db
def test_client_can_list_orders() -> None:
    first_order = Order()
    second_order = Order()

    repository = DjangoOrderRepository()
    repository.remember(first_order)
    repository.remember(second_order)

    api_client = APIClient()
    list_orders_url = reverse("order-list")

    response = api_client.get(list_orders_url)  # type: ignore

    assert response.status_code == status.HTTP_200_OK  # type: ignore

    orders_by_id = {UUID(order["id"]): order for order in response.json()}

    assert orders_by_id == {
        first_order.id: {
            "id": str(first_order.id),
            "status": "draft",
        },
        second_order.id: {
            "id": str(second_order.id),
            "status": "draft",
        },
    }
