from uuid import uuid4

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from novatrade.adapters.django.order_app.models import OrderPlacedRecord
from novatrade.adapters.django.order_app.persistence.order_repository import (
    DjangoOrderRepository,
)
from novatrade.domain.order import Order, OrderStatus


@pytest.fixture
def api_client() -> APIClient:
    """Provide an API client for end-to-end HTTP requests."""
    return APIClient()


@pytest.fixture
def order() -> Order:
    """Provide an existing Order that can be placed."""
    order = Order()
    order.add_product(
        product_id="BOOK-123",
        quantity=2,
    )

    repository = DjangoOrderRepository()
    repository.remember(order)

    return order


@pytest.fixture
def place_order_url(order: Order) -> str:
    """Provide the API URL for placing the Order."""
    return reverse(
        "order-place",
        kwargs={"order_id": order.id},
    )


@pytest.mark.django_db
def test_client_can_place_order(
    api_client: APIClient,
    order: Order,
    place_order_url: str,
) -> None:
    response = api_client.post(  # type: ignore
        place_order_url,
        format="json",
    )

    persisted_order = DjangoOrderRepository().get(order.id)
    persisted_event = OrderPlacedRecord.objects.get(
        order_id=order.id,
    )

    assert response.status_code == status.HTTP_200_OK  # type: ignore
    assert persisted_order.status is OrderStatus.PLACED
    assert persisted_event.order_id == order.id


@pytest.mark.django_db
def test_client_receives_not_found_when_order_does_not_exist(
    api_client: APIClient,
) -> None:
    unknown_order_id = uuid4()
    place_order_url = reverse(
        "order-place",
        kwargs={"order_id": unknown_order_id},
    )

    response = api_client.post(  # type: ignore
        place_order_url,
        format="json",
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND  # type: ignore
