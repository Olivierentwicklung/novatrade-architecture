# Architecture Journal 008 — Remembering Orders

## Context

By the end of Chapter 9, NovaTrade had its first explicit Application use case:

```python
place_order(order)
```

The Application knew when to ask the Domain to place an Order, while the Domain remained responsible for deciding whether placement was valid.

This exposed an important limitation. The use case assumed that somebody had already obtained the `Order` object.

A real caller is more likely to know an Order's identity than to hold a Python Domain object. Chapter 8 had already introduced stable Order identity, so the next business requirement became:

> An Order that has been remembered can later be retrieved by its identity.

At this point, no database, ORM, Repository pattern, or persistence framework was assumed.

## First Decision — Remember Orders in the Simplest Possible Way

The first implementation used an in-memory dictionary keyed by Order identity.

It supported two operations:

```python
remember(order)
get(order_id)
```

This was intentionally simple. The goal was not to design the persistence architecture upfront, but to discover what behavior the Application actually required.

The first test proved that an Order could be remembered and later retrieved by its identity.

## Placing an Order by Identity

Once Orders could be retrieved, the `place_order` use case no longer needed the caller to provide an `Order` object directly.

The Application could instead receive an Order identity:

```python
place_order(
    order_id=order.id,
    orders=orders,
)
```

The use case then coordinated the operation:

```python
order = orders.get(order_id)
order.place()
```

This made the Application layer responsible for locating the correct Aggregate, while the Domain remained responsible for enforcing the business rules of placement.

The dependency direction remained:

```text
Application
     │
     ▼
   Domain
```

The Application coordinates. The Domain decides.

## Pressure on the Concrete Dependency

Initially, `place_order` depended directly on the concrete in-memory `Orders` class.

However, the use case did not actually care that Orders were stored in a dictionary. It only required the ability to obtain an Order by identity.

A test double implementing only:

```python
get(order_id) -> Order
```

worked correctly at runtime because Python supports structural behavior through duck typing.

Static analysis exposed a different problem: the function annotation still required the concrete `Orders` class.

The runtime dependency and the declared type dependency therefore disagreed.

This pressure led to the introduction of an `OrderReader` Protocol describing only the capability the use case required at that moment:

```python
get(order_id) -> Order
```

No Repository abstraction was introduced yet.

## New Pressure — Changed State Must Be Preserved

The in-memory implementation concealed another assumption.

Retrieving an Order returned the same Python object held by the dictionary. Calling:

```python
order.place()
```

therefore appeared to update the stored Order automatically.

That behavior cannot be assumed for persistent storage. A storage implementation may reconstruct an Order from persisted data, meaning that changing the loaded Domain object does not automatically preserve the new state.

The business requirement therefore became:

> When an Order is placed, its changed state must be remembered.

A spy test demonstrated that `place_order` retrieved and modified the Order but never explicitly asked for the changed state to be preserved.

The test failed because no Order had been remembered after placement.

This was the pressure that made the read-only `OrderReader` abstraction insufficient.

## Decision — Introduce an Order Repository

The Application now required two related capabilities:

```python
get(order_id) -> Order
remember(order) -> None
```

At this point, the Repository abstraction had earned its place.

`OrderRepository` was introduced as a Protocol representing the collection-like boundary through which the Application retrieves and preserves Orders.

The use case became:

```python
order = orders.get(order_id)
order.place()
orders.remember(order)
```

The Repository does not decide whether the Order may be placed. That rule remains entirely inside the Domain.

The Repository is responsible only for making the Aggregate available to the Application and preserving its changed state.

## Why a Protocol?

The Application should depend on the capability it requires rather than on one storage implementation.

Using a Protocol allows implementations to satisfy the contract structurally. They do not need to inherit from a framework-specific or infrastructure-specific base class.

This keeps the Application independent of the mechanism used to store Orders.

## The In-Memory Implementation

The original dictionary-backed implementation was eventually renamed:

```text
InMemoryOrderRepository
```

The new name makes its responsibility explicit.

It is not _the_ Order storage mechanism. It is one implementation of the `OrderRepository` contract.

Its storage remains intentionally simple:

```python
dict[UUID, Order]
```

No database has been introduced.

## Why No Adapter Package Yet?

Although `InMemoryOrderRepository` can conceptually be understood as an adapter to the `OrderRepository` port, no separate `adapters` package was introduced.

There is currently only one concrete storage mechanism, and the existing package structure does not yet create enough pressure to justify another architectural boundary.

Creating that structure merely because a later implementation may need it would violate the principle guiding this project:

> No pattern without pressure.

The physical package structure can evolve when another storage mechanism makes the distinction necessary.

## Alternatives Considered

### Pass `Order` Objects Directly

This was the Chapter 9 design.

It was rejected for the new requirement because real Application callers naturally identify existing Orders by identity rather than by holding Domain objects.

### Depend Directly on the In-Memory Collection

This initially worked, but coupled the use case to a dictionary-backed implementation even though the use case required only storage capabilities.

The static type contract exposed this unnecessary coupling.

### Keep Only `OrderReader`

This accurately represented the first retrieval requirement.

It became insufficient once the Application was required to explicitly preserve the changed Order.

### Introduce `OrderRepository` Immediately

This was deliberately avoided.

The Repository pattern was introduced only after both retrieval and preservation had been demonstrated as concrete requirements.

### Introduce Django Persistence

Deferred.

No requirement in this chapter demands Django or a relational database.

### Introduce a Unit of Work

Deferred.

The chapter has not yet produced transaction-boundary pressure. Introducing a Unit of Work here would solve a problem the code has not encountered.

## Consequences

The Application layer now operates on existing Orders through an explicit persistence contract.

The use case can be described as:

```text
Order ID
   │
   ▼
Application
   │
   ▼
Repository.get(...)
   │
   ▼
Order
   │
   ▼
Domain behavior
   │
   ▼
Repository.remember(...)
```

The Domain remains independent of persistence.

The Application depends on a Repository contract rather than a concrete storage technology.

The in-memory implementation remains deliberately simple.

The system still has no real durable persistence mechanism.

That limitation remains visible rather than being hidden behind premature infrastructure.

## Evidence

At the end of the implementation work for this chapter:

```text
40 tests passed
```

The suite verifies the Domain behavior established in previous chapters together with the new Application and Repository behavior introduced here.

## Principle

The Repository was not introduced because it is a familiar architectural pattern.

It was introduced because the Application first needed to retrieve an Order by identity and later needed to preserve its changed state.

The pattern followed the pressure.

**No pattern without pressure.**
