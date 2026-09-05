from django.urls import path

from novatrade.adapters.django.order_app.api.views import (
    OrderDetailView,
    OrderListView,
    PlaceOrderView,
)

urlpatterns = [
    path(
        "orders/",
        OrderListView.as_view(),
        name="order-list",
    ),
    path(
        "orders/<uuid:order_id>/",
        OrderDetailView.as_view(),
        name="order-detail",
    ),
    path(
        "orders/<uuid:order_id>/place/",
        PlaceOrderView.as_view(),
        name="order-place",
    ),
]
