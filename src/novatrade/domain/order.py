class CannotPlaceEmptyOrder(Exception):
    """Raised when attempting to place an Order without any products."""


class InvalidQuantity(Exception):
    """Raised when a Product Quantity is not positive."""


class Order:
    """Represents a customer Order in the NovaTrade ordering domain."""

    def __init__(self) -> None:
        """Create an empty Order."""
        self.lines: list[tuple[str, int]] = []

    def add_product(self, product_id: str, quantity: int) -> None:
        """Add a Product with a positive Quantity to the Order."""
        if quantity <= 0:
            raise InvalidQuantity

        self.lines.append((product_id, quantity))

    def place(self) -> None:
        """Place the Order or reject it when it is empty."""
        raise CannotPlaceEmptyOrder

    def change_quantity(self, product_id: str, quantity: int) -> None:
        """Change the Quantity of a Product in the Order."""
        for index, (current_product_id, _) in enumerate(self.lines):
            if current_product_id == product_id:
                self.lines[index] = (product_id, quantity)
                return

    def quantity_for(self, product_id: str) -> int | None:
        """Return the Quantity of a Product in the Order."""
        for current_product_id, quantity in self.lines:
            if current_product_id == product_id:
                return quantity

        return None
