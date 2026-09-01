# Order Aggregate

## Context

NovaTrade allows Customers to modify an Order while they are preparing it.

Products can be added, their Quantities can be changed, and Products can be removed.

Once the Customer places the Order, however, its submitted contents must no longer change.

The Domain therefore needs to preserve the consistency of the Order and its Order Lines across every operation that can modify them.

## Pressure

The lifecycle rule first appeared when adding a Product after placement had to be rejected.

The same rule was then required when changing a Product's Quantity.

A further problem became visible when the Order exposed its internal collection of Order Lines: outside code could bypass the business operations and mutate the collection directly.

Finally, Product removal introduced a third modification operation that had to obey the same lifecycle rule.

The Domain was therefore facing two related pressures:

1. Multiple business operations needed to enforce the same modification invariant.
2. Outside code must not be able to bypass those operations by directly mutating the Order's internal collection.

The rule was larger than any individual method:

> Once an Order has been placed, its lines cannot be modified.

## Decision

`Order` controls all modifications to its Order Lines.

Operations that change the contents of an Order go through the Order itself:

```text id="thd6w7"
Order
  │
  ├── add_product()
  ├── change_quantity()
  └── remove_product()
```

The common lifecycle invariant is centralized internally:

```python id="q3mt0e"
def _ensure_modifiable(self) -> None:
    """Ensure that the Order can still be modified."""
    if self.is_placed:
        raise CannotModifyPlacedOrder
```

The internal Order Line collection remains mutable because the Order needs to perform its business operations:

```python id="1qgt7j"
self._lines: list[OrderLine] = []
```

But callers do not receive that mutable collection.

The public representation is immutable:

```python id="e0ykdp"
@property
def lines(self) -> tuple[OrderLine, ...]:
    """Return the Order Lines without exposing the mutable collection."""
    return tuple(self._lines)
```

`OrderLine` also remains an immutable Value Object.

As a result, modifications to the Order's contents are controlled by `Order`.

## Architectural Discovery

The following concepts must remain consistent together:

```text id="lx67pi"
Order
  │
  └── OrderLine
        │
        └── Quantity
```

Their business invariants include:

- Quantity must be positive.
- A Product appears at most once in an Order.
- Adding the same Product again increases its Quantity.
- Order Lines are immutable values.
- Once an Order has been placed, its Order Lines cannot change.

These rules create a consistency boundary.

```text id="xtf43b"
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

`Order` is the controlled entry point to that boundary.

Therefore:

> **Order is the Aggregate Root.**

This terminology was introduced only after the responsibility had emerged from concrete business pressure.

## Why

The Aggregate was not introduced because the project decided in advance to use Domain-Driven Design patterns.

The responsibility emerged because several business operations had to preserve rules spanning the Order and its contents.

Centralizing those rules in `Order` makes it harder for callers to create states that the Domain itself considers invalid.

The Aggregate Root therefore describes a responsibility already present in the model rather than introducing a new technical layer.

## What We Deliberately Did Not Add

### AggregateRoot Base Class

We did not introduce:

```python id="flhhxu"
class AggregateRoot:
    pass
```

`Order` is an Aggregate Root because of its responsibility, not because it inherits from a type with that name.

There is currently no behavior that would justify such a base class.

### Aggregate Interface

There is only one Aggregate requiring this responsibility.

No abstraction is needed merely to classify it.

### Generic State Machine

The current lifecycle requires only two conditions:

```text id="syfsxy"
not placed
placed
```

A generic State Machine would solve a problem the Domain does not yet have.

### OrderStatus

We deliberately retain the current boolean representation:

```python id="dgb7vj"
is_placed: bool
```

The Domain has not yet experienced enough lifecycle complexity to justify replacing it.

### Product Inside the Aggregate

An Order Line currently needs only the Product identifier.

The Product's own lifecycle and behavior do not need to be part of the Order consistency boundary.

### Mutable OrderLine API

`OrderLine` remains immutable.

Changes to an Order Line's Quantity happen through `Order.change_quantity()` so that the Aggregate Root can protect the Order's lifecycle invariant.

## Consequences

Outside code should interact with the Order through its business operations rather than manipulating its internal state.

This gives the Domain a clear modification boundary:

```text id="0w04ja"
Outside
   │
   ▼
 Order
   │
   ├── validates operation
   ├── protects lifecycle
   └── changes internal state
            │
            ▼
        OrderLine
            │
            ▼
         Quantity
```

The design also creates a useful constraint for future development:

> New operations that modify an Order's contents must preserve the invariants controlled by the Order.

The model therefore begins to guide subsequent changes instead of relying on every caller to remember the rules.

## Current Lifecycle Representation

The Order currently records placement with:

```python id="11nfsk"
is_placed = False
```

and:

```python id="d00d1e"
is_placed = True
```

This is sufficient for the business distinction currently required:

```text id="msvp5q"
Not Placed
    │
    │ place
    ▼
  Placed
```

We should not replace this representation merely because an Enum or State pattern appears more architectural.

## Open Pressure

NovaTrade now needs another business operation:

> **Confirm Order.**

The lifecycle will therefore begin moving toward:

```text id="a7aycz"
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

Cancellation may introduce another legal transition.

At that point, a single placement boolean may no longer represent the lifecycle safely.

That pressure is intentionally left unresolved.

It belongs to the next architectural decision.

---

**Decision status:** Accepted for Chapter 6

**Architectural principle:** No pattern without pressure.

**Discovered pattern:** Aggregate / Aggregate Root

**Aggregate Root:** `Order`

**Current verification:** 21 tests passing
