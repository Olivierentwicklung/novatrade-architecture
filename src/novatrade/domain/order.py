class CannotPlaceEmptyOrder(Exception):
    """Raised when attempting to place an Order without any products."""


class Order:
    """Represents a customer Order in the NovaTrade ordering domain."""

    def __init__(self) -> None:
        """Create an empty Order."""
        self.lines: list[tuple[str, int]] = []

    def add_product(self, product_id: str, quantity: int) -> None:
        """Add a Product and its Quantity to the Order."""
        self.lines.append((product_id, quantity))

    def place(self) -> None:
        """Place the Order or reject it when it is empty."""
        raise CannotPlaceEmptyOrder
