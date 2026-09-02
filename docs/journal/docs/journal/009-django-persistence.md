# Architecture Journal 009 — Django Persistence

## Context

NovaTrade can retrieve and preserve Orders through the `OrderRepository` contract introduced by the Application layer.

Until now, the concrete implementation has been `InMemoryOrderRepository`, which stores Orders in a Python dictionary. That implementation satisfies the Application's contract while the process is running, but its contents disappear when the process ends.

NovaTrade now has a new requirement:

> Orders must survive beyond the lifetime of the running application.

This introduces the first need for durable persistence.

## Pressure

The existing in-memory implementation cannot satisfy the new requirement because process memory is temporary.

NovaTrade needs a persistence mechanism capable of storing an Order outside the running Python process and retrieving it later by identity.

The Application already defines what it needs through `OrderRepository`:

```text
Application
     │
     ▼
OrderRepository
```

The new persistence technology should therefore satisfy this existing boundary rather than force the Domain or Application to adopt framework-specific abstractions.

## Decision

Use Django as a persistence adapter.

Django is placed physically inside the adapter layer:

```text
novatrade/
├── domain/
├── application/
└── adapters/
    └── django/
        ├── core/
        └── persistence/
```

The Domain and Application remain independent of Django.

The Django adapter implements the persistence behavior required by `OrderRepository` and translates between Domain objects and Django ORM representations.

The dependency direction is:

```text
Domain
     │
     ▼
Application
     │
     ▼
OrderRepository
     ▲
     │
DjangoOrderRepository
     │
     ▼
Django ORM
     │
     ▼
Database
```

Django therefore depends on concepts defined toward the center of the application. The Domain does not depend on Django.

## Persistence Representation

The Domain already contains the business concepts `Order`, `OrderLine`, and `Quantity`.

These objects should not become Django models merely because durable persistence is now required.

Instead, the Django adapter introduces separate persistence representations:

```text
Domain                     Persistence

Order                      OrderRecord
OrderLine                  OrderLineRecord
Quantity                   integer field
```

`OrderRecord` and `OrderLineRecord` exist to represent Domain state in the database. They are not replacements for the Domain objects.

This distinction is intentional.

`Order` owns business behavior such as placing, confirming, and cancelling an Order. `OrderRecord` describes how part of that state is represented through the Django ORM.

The persistence representation may therefore evolve according to storage requirements without allowing those requirements to define the business model.

## Repository Translation

`DjangoOrderRepository` forms the translation boundary between the two representations.

When preserving an Order, it translates Domain state into Django persistence state:

```text
Order.id             → OrderRecord.id
Order.status         → OrderRecord.status
OrderLine.product_id → OrderLineRecord.product_id
Quantity.value       → OrderLineRecord.quantity
```

When retrieving an Order, the repository performs the reverse translation and returns a Domain `Order` to the Application.

The Application therefore continues to work with the same `OrderRepository` abstraction regardless of whether Orders are stored in memory or through Django.

## Testing the Boundary

The Django repository is covered by an integration test rather than a Domain unit test.

The test requires an Order containing a product to be preserved and retrieved with its identity, status, and quantity intact.

`pytest-django` provides an isolated test database for this boundary.

The completed Chapter 11 implementation passes the entire test suite:

```text
41 passed
```

The existing Domain and Application tests continue to pass after Django is introduced.

This provides an important architectural check: adding a framework at the edge did not require rewriting the business model around that framework.

## An Uncomfortable Detail

Retrieving a placed Order currently requires the repository to reconstruct its status.

The simplest implementation does this by calling the existing business behavior:

```python
if order_record.status == "placed":
    order.place()
```

The implementation passes the current tests, but it exposes a distinction that the design does not yet express clearly.

The database is describing something that already happened:

```text
This Order was placed.
```

Calling `place()` expresses something different:

```text
Place this Order now.
```

Those operations happen to produce the same state in the current model, but they do not necessarily represent the same intention.

This tension is deliberately left unresolved.

The persistence adapter is working, and the requirement for durable Orders has been satisfied. A new architectural pressure has now become visible through the implementation itself.

## Consequences

Django can now provide durable persistence without owning the NovaTrade business model.

The Domain remains framework-independent.

The Application continues to depend on `OrderRepository`, not Django.

Django ORM classes are treated as persistence representations rather than Domain Entities.

Persistence mapping is explicit inside the adapter.

Integration testing now verifies the real persistence boundary using an isolated database.

The implementation also reveals that reconstructing previously stored Domain state is not necessarily the same operation as executing the business behavior that originally produced that state.

That distinction has not been designed away prematurely. It remains visible as pressure for the architecture to respond to when the system requires it.
