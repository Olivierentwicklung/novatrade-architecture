from django.apps import AppConfig


class OrderAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "novatrade.adapters.django.order_app"
    label = "persistence"
