from django.urls import path

from novatrade.adapters.django.order_app.api.views import PlaceOrderView

urlpatterns = [
    path(
        "orders/<uuid:order_id>/place/",
        PlaceOrderView.as_view(),
        name="order-place",
    ),
]
