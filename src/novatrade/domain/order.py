from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from novatrade.domain.events import OrderPlaced
from novatrade.domain.quantity import Quantity


class OrderStatus(Enum):
    """Represents the lifecycle status of an Order."""

    DRAFT = "draft"
    PLACED = "placed"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class CannotPlaceEmptyOrder(Exception):
    """Raised when attempting to place an Order without any products."""


class CannotModifyPlacedOrder(Exception):
    """Raised when attempting to modify a placed Order."""


class CannotConfirmUnplacedOrder(Exception):
    """Raised when attempting to confirm an Order before placement."""


class CannotCancelUnplacedOrder(Exception):
    """Raised when attempting to cancel an Order before placement."""


class CannotCancelConfirmedOrder(Exception):
    """Raised when attempting to cancel a confirmed Order."""


class CannotCancelCancelledOrder(Exception):
    """Raised when attempting to cancel an already cancelled Order."""


@dataclass(frozen=True)
class OrderLine:
    """Represents a Product and its Quantity within an Order."""

    product_id: str
    quantity: Quantity


class Order:
    """Represents a customer Order in the NovaTrade ordering domain."""

    def __init__(
        self,
        order_id: UUID | None = None,
        created_at: datetime | None = None,
    ) -> None:
        """Create an empty Order with a new or existing identity."""
        self.id = order_id if order_id is not None else uuid4()
        self.created_at = created_at
        self._lines: list[OrderLine] = []
        self.status = OrderStatus.DRAFT
        self.placed_at: datetime | None = None
        self._events: list[OrderPlaced] = []

    @property
    def lines(self) -> tuple[OrderLine, ...]:
        """Return the Order Lines without exposing the mutable collection."""
        return tuple(self._lines)

    @property
    def events(self) -> tuple[OrderPlaced, ...]:
        """Return facts recorded when this Order was placed."""
        return tuple(self._events)

    @classmethod
    def reconstitute(
        cls,
        order_id: UUID,
        status: OrderStatus,
        placed_at: datetime | None,
        lines: tuple[OrderLine, ...],
    ) -> "Order":
        """Reconstitute an existing Order from its historical state."""
        order = cls(order_id=order_id)
        order._lines = list(lines)
        order.status = status
        order.placed_at = placed_at
        return order

    def __eq__(self, other: object) -> bool:
        """Compare Orders by their identity."""
        if not isinstance(other, Order):
            return NotImplemented

        return self.id == other.id

    def add_product(self, product_id: str, quantity: int) -> None:
        """Add a Product to the Order."""

        self._ensure_modifiable()

        added_quantity = Quantity(quantity)

        for index, line in enumerate(self._lines):
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

        self._ensure_modifiable()

        new_quantity = Quantity(quantity)

        for index, line in enumerate(self._lines):
            if line.product_id == product_id:
                self._lines[index] = OrderLine(
                    product_id=product_id,
                    quantity=new_quantity,
                )
                return

    def quantity_for(self, product_id: str) -> int | None:
        """Return the Quantity of a Product in the Order."""
        for line in self._lines:
            if line.product_id == product_id:
                return line.quantity.value

        return None

    def place(self, placed_at: datetime) -> None:
        """Place the Order at the given time or reject it when it is empty."""
        if not self._lines:
            raise CannotPlaceEmptyOrder

        self.status = OrderStatus.PLACED
        self.placed_at = placed_at
        self._events.append(
            OrderPlaced(
                order_id=self.id,
                placed_at=placed_at,
            )
        )

    def remove_product(self, product_id: str) -> None:
        """Remove a Product from the Order."""

        self._ensure_modifiable()

        for index, line in enumerate(self._lines):
            if line.product_id == product_id:
                del self._lines[index]
                return

    def _ensure_modifiable(self) -> None:
        """Ensure that the Order can still be modified."""
        if self.status is not OrderStatus.DRAFT:
            raise CannotModifyPlacedOrder

    def confirm(self) -> None:
        """Confirm the Order or reject it when it has not been placed."""
        if self.status is not OrderStatus.PLACED:
            raise CannotConfirmUnplacedOrder

        self.status = OrderStatus.CONFIRMED

    def cancel(self) -> None:
        """Cancel the Order when its current state allows cancellation."""
        if self.status is OrderStatus.DRAFT:
            raise CannotCancelUnplacedOrder

        if self.status is OrderStatus.CONFIRMED:
            raise CannotCancelConfirmedOrder

        if self.status is OrderStatus.CANCELLED:
            raise CannotCancelCancelledOrder

        self.status = OrderStatus.CANCELLED

    def collect_events(self) -> tuple[OrderPlaced, ...]:
        """Return and clear Domain Events recorded by this Order."""
        events = tuple(self._events)
        self._events.clear()
        return events
