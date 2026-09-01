from dataclasses import dataclass


class InvalidQuantity(Exception):
    """Raised when a Quantity is not a positive integer."""


@dataclass(frozen=True)
class Quantity:
    """Represents a positive product Quantity."""

    value: int

    def __post_init__(self) -> None:
        """Ensure that the Quantity contains a positive integer."""
        if type(self.value) is not int or self.value <= 0:
            raise InvalidQuantity
