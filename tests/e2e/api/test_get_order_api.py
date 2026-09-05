import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from novatrade.adapters.django.order_app.persistence.order_repository import (
    DjangoOrderRepository,
)
from novatrade.domain.order import Order


@pytest.mark.django_db
def test_client_can_get_order() -> None:
    order = Order()
    DjangoOrderRepository().remember(order)

    api_client = APIClient()
    get_order_url = reverse(
        "order-detail",
        kwargs={"order_id": order.id},
    )

    response = api_client.get(get_order_url)  # type: ignore

    assert response.status_code == status.HTTP_200_OK  # type: ignore
    assert response.json() == {
        "id": str(order.id),
        "status": "draft",
    }
