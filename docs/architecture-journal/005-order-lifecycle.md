# Architecture Journal 005 — Order Lifecycle

## Context

At the end of Chapter 6, NovaTrade's `Order` had begun to protect its own consistency rules. An Order could be modified while it was being prepared, but once it had been placed, its lines could no longer be changed.

The lifecycle was represented by a single boolean:

```python
self.is_placed = False
```

That representation was sufficient for the business rules known at the time. There was no reason yet to introduce a more elaborate lifecycle model.

Chapter 7 introduced new business operations: confirmation and cancellation.

## Pressure

The first new requirement was:

> After a Customer places an Order, NovaTrade can confirm it.

The smallest implementation introduced another boolean:

```python
self.is_confirmed = False
```

This immediately created a new business rule: an Order could not be confirmed before it had been placed.

Cancellation introduced the same kind of pressure. A placed Order could be cancelled, which initially led to:

```python
self.is_cancelled = False
```

Further requirements established that:

- an unplaced Order cannot be cancelled;
- a confirmed Order cannot be cancelled;
- an already cancelled Order cannot be cancelled again.

The model was now using three independent booleans:

```python
self.is_placed = False
self.is_confirmed = False
self.is_cancelled = False
```

These booleans did not represent three independent business facts. Together, they attempted to describe one business process.

Three independent booleans can represent eight combinations, including combinations that do not correspond to valid NovaTrade Order states.

For example:

```text
is_placed     = False
is_confirmed  = True
is_cancelled  = True
```

The business did not have an Order in such a state.

The growing transition logic also showed that operations were no longer asking isolated yes-or-no questions. They were asking a different question:

> What is the current lifecycle state of this Order, and is this operation allowed from that state?

## Decision

Represent the Order lifecycle explicitly with `OrderStatus`:

```python
class OrderStatus(Enum):
    """Represents the lifecycle status of an Order."""

    DRAFT = "draft"
    PLACED = "placed"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
```

A new Order begins in one state:

```python
self.status = OrderStatus.DRAFT
```

The previous lifecycle booleans are removed.

`Order.status` becomes the single source of truth for the Order lifecycle.

## Lifecycle

The currently known lifecycle is:

```text
                    confirm()
                 ┌────────────► CONFIRMED
                 │
DRAFT ──place()──► PLACED
                 │
                 └──cancel()──► CANCELLED
```

The transitions are performed through behavior on the `Order` Aggregate Root.

The current business rules allow:

```text
DRAFT  ──place()───► PLACED
PLACED ──confirm()─► CONFIRMED
PLACED ──cancel()──► CANCELLED
```

Other discovered transitions are rejected by the Domain.

## Why

The important decision is not simply to replace booleans with an Enum.

The deeper decision is to model the lifecycle as one business concept rather than as several independent technical flags.

With separate booleans, the code could represent contradictory combinations. It also required business methods to interpret combinations of flags in order to determine what an Order actually meant.

With `OrderStatus`, an Order occupies exactly one lifecycle state at a time.

Code can therefore reason directly in the language of the business:

```python
if self.status is not OrderStatus.PLACED:
```

rather than reconstructing a state from combinations such as:

```python
if not self.is_placed or self.is_confirmed or self.is_cancelled:
```

The model now more closely matches the process described by NovaTrade.

## Aggregate Protection

The lifecycle also strengthens the consistency boundary discovered in Chapter 6.

Order contents may be modified only while the Order is in `DRAFT`:

```python
def _ensure_modifiable(self) -> None:
    """Ensure that the Order can still be modified."""
    if self.status is not OrderStatus.DRAFT:
        raise CannotModifyPlacedOrder
```

The Aggregate Root therefore uses its lifecycle state to decide whether operations on its internal `OrderLine` collection are valid.

External code still cannot directly mutate the internal collection.

## Transition Rules

Confirmation is valid only from `PLACED`:

```python
def confirm(self) -> None:
    """Confirm the Order or reject it when it has not been placed."""
    if self.status is not OrderStatus.PLACED:
        raise CannotConfirmUnplacedOrder

    self.status = OrderStatus.CONFIRMED
```

Cancellation currently distinguishes the discovered invalid transitions and allows cancellation from `PLACED`:

```python
def cancel(self) -> None:
    """Cancel the Order when its current state allows cancellation."""
    if self.status is OrderStatus.DRAFT:
        raise CannotCancelUnplacedOrder

    if self.status is OrderStatus.CONFIRMED:
        raise CannotCancelConfirmedOrder

    if self.status is OrderStatus.CANCELLED:
        raise CannotCancelCancelledOrder

    self.status = OrderStatus.CANCELLED
```

These rules remain inside the Domain rather than being delegated to a controller, serializer, database model, or framework.

## Migration Strategy

`OrderStatus` was not introduced by replacing the existing implementation in one large change.

The lifecycle was migrated incrementally under tests.

First, a new Order received:

```python
self.status = OrderStatus.DRAFT
```

The existing booleans temporarily remained.

Each transition was then migrated separately:

```text
place()   → PLACED
confirm() → CONFIRMED
cancel()  → CANCELLED
```

During this period, the old booleans and the new status representation existed together temporarily.

Once all transitions were represented by `OrderStatus`, lifecycle decisions were changed to use `status`. The complete test suite remained green.

Only then were:

```text
is_placed
is_confirmed
is_cancelled
```

removed.

This allowed `OrderStatus` to become the single source of truth without performing an uncontrolled rewrite.

## Architectural Discovery

The important concept discovered in this chapter is an explicit business lifecycle.

The Order is not a collection of independent boolean properties. It moves through a constrained set of meaningful states, and business operations represent transitions between those states.

The resulting model is:

```text
Order
│
├── status: OrderStatus
│
├── place()
├── confirm()
└── cancel()
```

The state and the operations that change it remain controlled by the `Order` Aggregate Root.

## Deliberately Not Added

No generic State pattern was introduced.

There are no classes such as:

```text
DraftOrderState
PlacedOrderState
ConfirmedOrderState
CancelledOrderState
```

There is also no generic state-machine framework, transition engine, or `AggregateRoot` base class.

The current pressure does not justify those abstractions.

`OrderStatus` together with explicit behavior on `Order` is sufficient for the lifecycle currently known.

If future business rules make individual states substantially more complex, the design can evolve again under concrete pressure.

## Consequences

### Positive

- The Order lifecycle has one source of truth.
- Invalid combinations of lifecycle booleans are eliminated.
- Business transitions are explicit.
- Lifecycle rules remain inside the Domain.
- Aggregate modification rules can use the same lifecycle concept.
- The code speaks more directly in NovaTrade's business language.
- Future lifecycle requirements have a clear place to apply pressure.

### Trade-offs

- `Order` now knows about several lifecycle transitions.
- Exception names reflect the business rules discovered incrementally and may need to evolve if the vocabulary changes.
- `OrderStatus` introduces an explicit state model that persistence adapters will eventually need to store and reconstruct.
- More complex future lifecycle behavior may eventually create pressure for a richer design.

These trade-offs are accepted because they correspond to the business complexity currently present rather than hypothetical future complexity.

## Verification

The final Chapter 7 implementation was verified with the complete test suite:

```text
31 tests collected
31 passed
0 failed
```

Final verified execution:

```text
31 passed in 0.11s
```

The tests cover both previously established Aggregate behavior and the lifecycle behavior introduced in this chapter.

## Open Pressure

The Order now has behavior, protected internal state, and an explicit lifecycle.

What it still does not have is identity.

Two Orders may contain exactly the same Products and Quantities and may occupy the same lifecycle state, but the business still needs to distinguish one Order from another.

That pressure belongs to the next chapter.

## Decision Record

**Decision status:** Accepted for Chapter 7
**Architectural principle:** No pattern without pressure.
**Discovered concept:** Explicit Order lifecycle
**Lifecycle representation:** `OrderStatus`
**Lifecycle owner:** `Order` Aggregate Root
**Current states:** `DRAFT`, `PLACED`, `CONFIRMED`, `CANCELLED`
**Single source of truth:** `Order.status`
**Deliberately deferred:** State pattern and generic state-machine abstraction
**Executable verification:** 31 tests passing
