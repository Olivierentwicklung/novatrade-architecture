# Architecture Journal 002 — Quantity Becomes a Value Object

## Context

NovaTrade allows a Product to be added to a Draft Order with a Quantity.

The first implementation represented Quantity as a plain Python `int`:

```python
order.add_product(
    product_id="BOOK-123",
    quantity=2,
)
```

At this stage, a dedicated domain type was unnecessary. The primitive representation was simple and sufficient for the behavior the system needed.

The first additional business rule introduced a constraint:

> A Quantity must be positive.

The rule was initially enforced directly inside `Order.add_product()`:

```python
if quantity <= 0:
    raise InvalidQuantity
```

This was intentionally the simplest solution. There was still only one operation that needed the rule, so introducing a dedicated abstraction would have been premature.

The primitive was still enough.

## New Pressure

NovaTrade then introduced another operation:

> A Customer can change the Quantity of a Product while the Order is still Draft.

The first implementation of `change_quantity()` also accepted a plain integer:

```python
order.change_quantity(
    product_id="BOOK-123",
    quantity=5,
)
```

This worked for valid values, but a new test exposed an inconsistency.

While `add_product()` rejected a quantity of zero, `change_quantity()` could still introduce the same invalid value:

```python
order.change_quantity(
    product_id="BOOK-123",
    quantity=0,
)
```

The test failed because `InvalidQuantity` was not raised.

The problem was therefore larger than a missing validation check in one method.

Both operations were working with the same business concept, but the primitive `int` did not protect that concept.

## What the Primitive Could Not Express

Python allows many integer values:

```text
-5
0
1
2
100
```

But NovaTrade does not consider all of them valid Quantities.

For NovaTrade:

```text
Quantity(-5)   invalid
Quantity(0)    invalid
Quantity(1)    valid
Quantity(2)    valid
```

The primitive type could represent states that the business considered impossible.

The same invariant was also relevant wherever a Quantity entered the domain. Keeping that rule inside individual Order operations would require every operation to remember the same validation.

That was the architectural pressure.

The rule did not fundamentally belong to `add_product()` or `change_quantity()`.

It belonged to **Quantity**.

## Decision

Introduce `Quantity` as a domain Value Object in:

`src/novatrade/domain/quantity.py`

```python
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
```

The Value Object now owns the invariant:

> A NovaTrade Quantity must be a positive integer.

The `Order` no longer stores raw integers for quantities:

```python
self.lines: list[tuple[str, Quantity]] = []
```

When a Product is added, the primitive input is converted into the domain concept:

```python
self.lines.append(
    (product_id, Quantity(quantity))
)
```

Changing a Quantity goes through the same domain type:

```python
new_quantity = Quantity(quantity)
```

Both operations therefore rely on the same invariant.

There is now one authoritative place responsible for deciding whether a Quantity is valid.

## Why a Value Object?

Quantity now has meaning beyond the capabilities of a primitive integer.

It has a business invariant:

> A Quantity must be a positive integer.

It also has no independent identity.

Two Quantities representing the same number mean the same thing:

```python
Quantity(2) == Quantity(2)
```

They do not need to be the same Python object.

Their **value** determines their equality.

This is one of the defining characteristics of a Value Object.

## Immutability

`Quantity` is declared using:

```python
@dataclass(frozen=True)
```

This makes it immutable.

Once created:

```python
quantity = Quantity(2)
```

its value cannot later become:

```python
quantity.value = 0
```

This matters because the constructor establishes the invariant.

If the value could be changed freely afterward, a valid Quantity could become invalid without passing through the validation that created it.

Instead of mutating an existing Quantity, the domain creates another one:

```python
Quantity(5)
```

## Runtime Protection

The public type contract declares:

```python
value: int
```

Static type checking therefore communicates that callers should provide an integer.

The domain still protects itself at runtime:

```python
if type(self.value) is not int or self.value <= 0:
    raise InvalidQuantity
```

This rejects values such as:

```text
0
-1
1.5
True
```

The explicit runtime check is useful because Python's type annotations are not runtime enforcement.

The exact type check also prevents `bool` from being accepted as a Quantity. In Python, `bool` is a subclass of `int`, but `True` and `False` do not represent meaningful product quantities in the NovaTrade domain.

## Evidence

The decision emerged through executable tests rather than from an architectural plan.

The tests demonstrate that:

- a Product can be added to an Order with a valid Quantity
- zero is rejected
- negative Quantities are rejected
- a Product Quantity can be changed
- changing a Quantity cannot bypass the invariant
- non-integer runtime values are rejected
- boolean values are rejected
- two Quantities with the same value compare as equal
- a Quantity cannot be mutated after creation

After introducing the Value Object and refactoring `Order` to use it, the complete test suite remained green.

The architecture therefore changed while preserving the required business behavior.

## What We Learned

The important decision was not simply:

> Use a Value Object for Quantity.

The important part was **when** that decision became justified.

We did not begin by creating `Quantity`.

We began with:

```python
quantity: int
```

That was enough.

Then the business introduced a rule.

We added the simplest validation.

That was still enough.

Then another operation needed to work with the same concept, and the invariant could be bypassed.

Only then did the primitive representation become uncomfortable.

The progression was:

```text
int
    ↓
business rule
    ↓
local validation
    ↓
second operation
    ↓
invariant can be bypassed
    ↓
domain pressure
    ↓
Quantity Value Object
```

The architecture emerged from evidence.

## Trade-offs

Introducing `Quantity` creates an additional domain type.

Callers may need to construct a `Quantity`, and code that needs the underlying primitive value may need to access:

```python
quantity.value
```

This is more code than passing integers throughout the system.

The additional type is justified because it gives the business invariant one authoritative home and prevents invalid Quantity states from spreading through the domain model.

The small increase in structural complexity buys stronger domain guarantees.

## Deliberately Not Added

We did not introduce:

- a `ProductId` Value Object
- a generic `ValueObject` base class
- a validation framework
- arithmetic operators on `Quantity`
- a general-purpose domain primitive abstraction
- additional architectural layers

A `ProductId` Value Object might eventually become useful, but there is currently no business pressure that requires one.

Creating it merely because `Quantity` became a Value Object would be architecture by symmetry rather than architecture by evidence.

The same applies to a generic Value Object base class. One Value Object does not justify building a framework for Value Objects.

Our principle remains:

> **No pattern without pressure.**

## Open Pressure

The Order currently stores Product identifiers and Quantities together:

```python
list[tuple[str, Quantity]]
```

This representation is still simple enough for the behavior currently required.

But a tuple has very little domain meaning.

As NovaTrade begins asking more questions about the individual products contained in an Order, Product and Quantity may need to travel together as something more meaningful than:

```python
("BOOK-123", Quantity(2))
```

If that combination acquires its own rules, behavior, or language, another domain concept may earn its place.

We will not introduce it yet.

We will wait for the business to create the pressure.
