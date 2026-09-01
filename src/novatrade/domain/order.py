from dataclasses import dataclass

from novatrade.domain.quantity import Quantity


class CannotPlaceEmptyOrder(Exception):
    """Raised when attempting to place an Order without any products."""


class CannotModifyPlacedOrder(Exception):
    """Raised when attempting to modify a placed Order."""


@dataclass(frozen=True)
class OrderLine:
    """Represents a Product and its Quantity within an Order."""

    product_id: str
    quantity: Quantity


class Order:
    """Represents a customer Order in the NovaTrade ordering domain."""

    def __init__(self) -> None:
        """Create an empty Order."""
        self._lines: list[OrderLine] = []
        self.is_placed = False

    @property
    def lines(self) -> tuple[OrderLine, ...]:
        """Return the Order Lines without exposing the mutable collection."""
        return tuple(self._lines)

    def add_product(self, product_id: str, quantity: int) -> None:
        """Add a Product to the Order."""

        if self.is_placed:
            raise CannotModifyPlacedOrder

        added_quantity = Quantity(quantity)

        for index, line in enumerate(self.lines):
            if line.product_id == product_id:
                self._lines[index] = OrderLine(
                    product_id=product_id,
                    quantity=Quantity(line.quantity.value + added_quantity.value),
                )
                return

        self._lines.append(
            OrderLine(
                product_id=product_id,
                quantity=added_quantity,
            )
        )

    def change_quantity(self, product_id: str, quantity: int) -> None:
        """Change the Quantity of a Product in the Order."""

        if self.is_placed:
            raise CannotModifyPlacedOrder

        new_quantity = Quantity(quantity)

        for index, line in enumerate(self.lines):
            if line.product_id == product_id:
                self._lines[index] = OrderLine(
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
        if not self._lines:
            raise CannotPlaceEmptyOrder

        self.is_placed = True

    def remove_product(self, product_id: str) -> None:
        """Remove a Product from the Order."""
        if self.is_placed:
            raise CannotModifyPlacedOrder

        for index, line in enumerate(self._lines):
            if line.product_id == product_id:
                del self._lines[index]
                return
