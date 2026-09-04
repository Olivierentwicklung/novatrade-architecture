# Architecture Journal 013 — Domain Events as Business Facts

## Context

Placing an Order already changed its state from `DRAFT` to `PLACED` and recorded when the placement occurred. That was sufficient while the system only needed to know the Order's current state.

A new requirement introduced a different concern: NovaTrade must be able to recognize that an Order was successfully placed, including which Order was placed and when it happened.

This creates an important distinction between **state** and **something that happened**.

An Order loaded from persistence may already have the status `PLACED`. That does not mean it was placed during the current business operation.

## Pressure

The first implementation represented the new fact with ordinary data:

```python
{
    "order_id": order.id,
    "placed_at": placed_at,
}
```

The data was correct, but the representation had no explicit business meaning. Nothing in the type itself said:

> An Order was placed.

As this fact became part of the Domain language, the primitive representation was no longer expressive enough.

The Domain also needed to distinguish a newly produced fact from historical state:

```text
Historical state:
"This Order is already placed."

New Domain fact:
"This Order has just been placed."
```

## Decision

Introduce the immutable `OrderPlaced` Domain Event:

```python
@dataclass(frozen=True)
class OrderPlaced:
    order_id: UUID
    placed_at: datetime
```

`Order.place()` records `OrderPlaced` only after the placement succeeds.

```text
Order.place(placed_at)
        │
        ├── enforce business rules
        ├── change Order state
        └── record OrderPlaced
```

The aggregate exposes newly recorded events through:

```python
order.events
```

and allows pending events to be collected through:

```python
events = order.collect_events()
```

Collecting returns the recorded events and removes them from the aggregate's pending event collection.

The aggregate therefore owns the decision that a business fact occurred, while remaining unaware of what other parts of the system may eventually do with that fact.

## Historical State Does Not Produce New Events

`Order.reconstitute()` restores an Order's historical state without executing `Order.place()`.

Consequently, reconstituting an Order that is already `PLACED` does not produce a new `OrderPlaced` event.

This preserves the distinction:

```text
Order.reconstitute(status=PLACED)
        │
        └── historical state

Order.place(...)
        │
        └── new OrderPlaced fact
```

Loading existing data must not manufacture new business facts.

## Alternatives Considered

### Keep using a dictionary

A dictionary contains the necessary values but does not express the business concept. `OrderPlaced` gives the fact an explicit name in the Domain language.

### Infer the event from Order state

Inferring `OrderPlaced` from `status == PLACED` would confuse historical state with something that happened during the current operation.

### Create the event in the Application layer

The Application could create `OrderPlaced` after calling `order.place()`. However, the Domain owns the placement rules and knows whether placement actually succeeded. The fact therefore originates in the aggregate.

### Introduce a generic `DomainEvent` base class

There is currently only one event type and no behavior requiring polymorphism between different Domain Events. A generic hierarchy would solve a problem that has not appeared yet.

### Introduce an Event Bus

An Event Bus would answer a different question: how other parts of the system receive and react to Domain Events. The current pressure only requires the Domain to express what happened.

### Use Event Sourcing

Domain Events do not imply Event Sourcing. NovaTrade continues to persist the current state of an Order through its repository. The pending event collection represents newly produced facts, not the historical source from which the aggregate is reconstructed.

## Consequences

The Domain can now express both current state and newly produced business facts.

A successful placement records `OrderPlaced`. A failed placement does not, because the business fact never occurred. Reconstituting historical state also produces no new event.

Events can be collected from the aggregate without the aggregate knowing who will consume them or what reaction they may cause.

This establishes a clear boundary between:

```text
Something happened.
```

and:

```text
Something should happen because of it.
```

## What We Are Not Introducing

This decision deliberately does not introduce:

- an Event Bus or dispatcher,
- event handlers,
- publishers or subscribers,
- asynchronous processing or queues,
- an event store or Event Sourcing,
- a generic `DomainEvent` hierarchy,
- transaction-aware event dispatch.

Those mechanisms require additional pressure before they earn a place in the architecture.

## Principle

A Domain Event represents a business fact produced by successful Domain behavior. It is not merely another representation of the aggregate's current state.

**The aggregate says what happened. It does not decide who should care.**
