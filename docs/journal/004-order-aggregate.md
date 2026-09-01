# Order Aggregate

## Context

NovaTrade allows Customers to modify an Order while they are preparing it. Products can be added, their Quantities can be changed, and Products can be removed.

Once the Customer places the Order, however, its submitted contents must no longer change.

The Domain therefore needs to preserve the consistency of the Order and its Order Lines across every operation that can modify them.

## Pressure

The lifecycle rule first appeared when adding a Product after placement had to be rejected. The same rule was then required when changing the Quantity of an existing Product.

A further problem became visible when the Order exposed its internal collection of Order Lines. Outside code could bypass the protected business operations and mutate the collection directly, which meant that protecting `add_product()` and `change_quantity()` alone was not enough.

Finally, Product removal introduced a third modification operation that had to obey the same lifecycle rule.

The Domain was therefore facing two related pressures:

1. Multiple business operations needed to enforce the same modification invariant.
2. Outside code must not be able to bypass those operations by directly mutating the Order's internal collection.

The rule was larger than any individual method:

> **Once an Order has been placed, its lines cannot be modified.**

## Decision

`Order` owns its Order Lines and controls all modifications to them.

Operations that change the contents of an Order go through the Order itself:

```text id="z7c3np"
Order
  │
  ├── add_product()
  ├── change_quantity()
  └── remove_product()
```

The common lifecycle invariant is centralized internally:

```python id="g5x1kw"
def _ensure_modifiable(self) -> None:
    """Ensure that the Order can still be modified."""
    if self.is_placed:
        raise CannotModifyPlacedOrder
```

The Order keeps its collection mutable internally because its business operations need to add, replace, and remove Order Lines:

```python id="b6q2ht"
self._lines: list[OrderLine] = []
```

Methods inside `Order` work directly with `_lines`. The public `lines` property exists for callers outside the Aggregate and does not expose that mutable collection:

```python id="m8v4ds"
@property
def lines(self) -> tuple[OrderLine, ...]:
    """Return the Order Lines without exposing the mutable collection."""
    return tuple(self._lines)
```

This gives the model a simple encapsulation rule:

```text id="t4n9fc"
Inside Order
    │
    └── _lines
          │
          │ exposed as
          ▼
        lines
          │
          ▼
tuple[OrderLine, ...]
          │
          ▼
     outside code
```

`OrderLine` remains an immutable Value Object. Changes to an Order's contents therefore happen through `Order`, allowing the Order to enforce its lifecycle rules before modifying its internal state.

## Architectural Discovery

The following concepts must remain consistent together:

```text id="p2r7kx"
Order
  │
  └── OrderLine
        │
        └── Quantity
```

Their business invariants include:

- a `Quantity` must be a positive integer;
- a Product appears at most once in an Order;
- adding the same Product again increases its Quantity;
- `OrderLine` is immutable;
- once an Order has been placed, its Order Lines cannot change.

These rules create a consistency boundary.

```text id="k5w8qm"
┌──────────────────────────────────┐
│              Order               │
│                                  │
│    ┌────────────────────────┐    │
│    │       OrderLine        │    │
│    │                        │    │
│    │ Product ID             │    │
│    │ Quantity               │    │
│    └────────────────────────┘    │
│                                  │
│   protects business invariants   │
└──────────────────────────────────┘
```

In Domain-Driven Design terminology, this consistency boundary is an **Aggregate**.

`Order` is the controlled entry point to that boundary. Outside code does not modify the Order Lines directly; modifications go through operations on `Order`.

Therefore:

> **Order is the Aggregate Root.**

This terminology was introduced only after the responsibility had emerged from concrete business pressure.

## Why

The Aggregate was not introduced because the project decided in advance to use Domain-Driven Design patterns. Its responsibility emerged because several business operations had to preserve rules spanning the Order and its contents.

Centralizing those rules in `Order` makes it harder for callers to create states that the Domain itself considers invalid. Keeping `_lines` private also prevents callers from bypassing the business operations that protect those rules.

The Aggregate Root therefore describes a responsibility already present in the model rather than introducing a new technical layer.

This follows the architectural principle used throughout NovaTrade:

> **No pattern without pressure.**

## Internal State and Public Representation

The distinction between `_lines` and `lines` is intentional.

Inside the Aggregate, `Order` owns its state and works directly with `_lines`:

```python id="d3j6vr"
for line in self._lines:
    ...
```

Outside the Aggregate, callers receive:

```python id="r9y5pb"
order.lines
```

which is represented as:

```python id="c7f2xn"
tuple[OrderLine, ...]
```

This prevents the mutable collection itself from escaping the Aggregate.

The final refactoring from internal uses of `self.lines` to `self._lines` did not change observable business behavior. The complete test suite therefore remained GREEN.

This illustrates an important TDD property: tests can protect the public behavior of the Domain while allowing its internal design to improve during refactoring.

## What We Deliberately Did Not Add

### AggregateRoot Base Class

We did not introduce:

```python id="h1m6vz"
class AggregateRoot:
    pass
```

and make `Order` inherit from it.

`Order` is an Aggregate Root because of its responsibility, not because it inherits from a type with that name. There is currently no shared behavior that would justify such a base class.

### Aggregate Interface

There is currently only one Aggregate requiring this responsibility. An interface would classify the concept without solving an existing problem.

We can introduce an abstraction later if concrete pressure requires one.

### Generic State Machine

The current lifecycle needs only two relevant conditions:

```text id="f8k3ts"
not placed
placed
```

A generic State Machine would solve a problem the Domain does not yet have.

### OrderStatus

The current implementation deliberately retains:

```python id="q4d7wj"
self.is_placed = False
```

and:

```python id="a6n2kr"
self.is_placed = True
```

The Domain has not yet experienced enough lifecycle complexity to justify replacing this representation.

### Product Inside the Aggregate

An `OrderLine` currently needs only the Product identifier:

```python id="y5p8cf"
product_id: str
```

The Product's own lifecycle and behavior do not need to participate in the consistency rules currently protected by `Order`.

There is therefore no reason to expand the Aggregate boundary to include a Product Entity.

### Mutable OrderLine API

`OrderLine` remains immutable:

```python id="s2v9md"
@dataclass(frozen=True)
class OrderLine:
    product_id: str
    quantity: Quantity
```

Changing the Quantity of a Product happens through:

```python id="u7k4fq"
order.change_quantity(...)
```

rather than through a mutation operation on `OrderLine`.

This keeps modification under the control of the Aggregate Root.

## Consequences

Outside code should interact with the Order through its business operations rather than manipulating its internal state.

```text id="e9r3kb"
Outside
   │
   ▼
 Order
   │
   ├── validates operation
   ├── protects lifecycle
   └── modifies internal state
            │
            ▼
        OrderLine
            │
            ▼
         Quantity
```

New operations that modify an Order's contents must preserve the invariants controlled by the Order.

This means the Domain Model itself begins to guide future development. A developer adding another modification operation should not need to rediscover independently that placed Orders must be protected; that responsibility is now explicit inside the Aggregate Root.

## Current Lifecycle Representation

The Order currently records placement with a boolean:

```python id="n6t1vx"
self.is_placed = False
```

Placement changes it to:

```python id="w8c5rp"
self.is_placed = True
```

For the current business requirements, this representation is sufficient:

```text id="b4m7qd"
Not Placed
    │
    │ place
    ▼
  Placed
```

Replacing the boolean with an Enum or State pattern merely because those representations appear more architectural would contradict the evolutionary approach used throughout the project.

The existing representation should remain until new business pressure proves that it is insufficient.

## Verification

The final Chapter 6 refactoring changed internal implementation details without changing observable business behavior.

The complete Domain test suite was executed with:

```bash id="v2j8kn"
python -m pytest -v
```

Result:

```text id="x5q9fm"
21 passed in 0.09s
```

The passing suite covers the Order and Quantity behavior accumulated so far, including:

- rejecting empty Order placement;
- adding Products;
- validating Quantities;
- changing Product Quantities;
- representing Order Lines explicitly;
- merging duplicate Products;
- Order Line equality and immutability;
- preventing Product addition after placement;
- preventing Quantity changes after placement;
- exposing Order Lines through an immutable collection;
- removing Products;
- preventing Product removal after placement;
- Quantity equality and immutability.

The tests verify observable Domain behavior while allowing internal implementation details to evolve safely during refactoring.

## Open Pressure

NovaTrade now needs another business operation:

> **Confirm Order.**

The lifecycle is therefore beginning to move beyond the distinction represented by `is_placed`:

```text id="c3z7hw"
Draft
  │
  │ place
  ▼
Placed
  │
  │ confirm
  ▼
Confirmed
```

Cancellation may eventually introduce another legal transition and additional rules.

At that point, independent booleans could allow combinations that do not correspond to meaningful business states. The current representation may therefore stop being sufficient.

We deliberately do not solve that problem here.

The next requirement must first create the pressure.

That belongs to Chapter 7.

---

**Decision status:** Accepted for Chapter 6

**Architectural principle:** No pattern without pressure.

**Discovered pattern:** Aggregate / Aggregate Root

**Aggregate:** `Order` + `OrderLine` + `Quantity`

**Aggregate Root:** `Order`

**Current lifecycle representation:** `is_placed: bool`

**Executable verification:** 21 tests passing
