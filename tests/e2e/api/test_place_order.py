from uuid import UUID, uuid4

import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    """Provide an API client for end-to-end HTTP requests."""
    return APIClient()


@pytest.fixture
def order_id() -> UUID:
    """Provide the identity of the Order used by the scenario."""
    return uuid4()


@pytest.fixture
def place_order_url(order_id: UUID) -> str:
    """Provide the API URL for placing the Order."""
    return reverse(
        "order-place",
        kwargs={"order_id": order_id},
    )


@pytest.mark.django_db
def test_client_can_request_order_placement(
    api_client: APIClient,
    place_order_url: str,
) -> None:
    response = api_client.post(place_order_url, format="json")

    assert response.status_code == 200
