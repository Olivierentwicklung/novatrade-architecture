from django.db import models


class OrderRecord(models.Model):
    """Persistent representation of a NovaTrade Order."""

    id = models.UUIDField(primary_key=True)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(null=True)
    placed_at = models.DateTimeField(null=True)


class OrderLineRecord(models.Model):
    """Persistent representation of a NovaTrade Order Line."""

    order = models.ForeignKey(
        OrderRecord,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    product_id = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()


class OrderPlacedRecord(models.Model):
    """Persistent representation of an OrderPlaced business fact."""

    order_id = models.UUIDField()
    placed_at = models.DateTimeField()
