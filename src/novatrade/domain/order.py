from dataclasses import dataclass

from novatrade.domain.quantity import Quantity


class CannotPlaceEmptyOrder(Exception):
    """Raised when attempting to place an Order without any products."""


@dataclass(frozen=True)
class OrderLine:
    """Represents a Product and its Quantity within an Order."""

    product_id: str
    quantity: Quantity


class Order:
    """Represents a customer Order in the NovaTrade ordering domain."""

    def __init__(self) -> None:
        """Create an empty Order."""
        self.lines: list[OrderLine] = []

    def add_product(self, product_id: str, quantity: int) -> None:
        """Add a Product to the Order."""
        added_quantity = Quantity(quantity)

        for index, line in enumerate(self.lines):
            if line.product_id == product_id:
                self.lines[index] = OrderLine(
                    product_id=product_id,
                    quantity=Quantity(line.quantity.value + added_quantity.value),
                )
                return

        self.lines.append(
            OrderLine(
                product_id=product_id,
                quantity=added_quantity,
            )
        )

    def change_quantity(self, product_id: str, quantity: int) -> None:
        """Change the Quantity of a Product in the Order."""
        new_quantity = Quantity(quantity)

        for index, line in enumerate(self.lines):
            if line.product_id == product_id:
                self.lines[index] = OrderLine(
                    product_id=product_id,
                    quantity=new_quantity,
                )
                return

    def quantity_for(self, product_id: str) -> int | None:
        """Return the Quantity of a Product in the Order."""
        for line in self.lines:
            if line.product_id == product_id:
                return line.quantity.value

        return None

    def place(self) -> None:
        """Place the Order or reject it when it is empty."""
        raise CannotPlaceEmptyOrder
