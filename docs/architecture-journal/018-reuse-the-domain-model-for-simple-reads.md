# 018 — Reuse the Domain Model for Simple Reads

## Context

NovaTrade could already place Orders through its HTTP API, but clients could
not retrieve an Order.

The first read requirement was deliberately small:

> Given an existing Order, when a client requests that Order by identity,
> return its identity and status.

The system already had an `OrderRepository` port capable of loading an Order
by identity, a Django implementation of that repository, and an `Order`
aggregate that could be reconstituted from persistence.

A separate read model, query service, DTO, or CQRS architecture could have
been introduced immediately. However, the requirement did not yet provide
enough pressure to justify those additional concepts.

## Decision

Reuse the existing `OrderRepository` and Domain `Order` for the first read
use case.

Introduce an Application use case:

`get_order(order_id, orders)`

The use case depends on the existing `OrderRepository` port and returns the
requested `Order`.

The HTTP adapter calls this Application capability through
`DjangoOrderRepository` and translates the returned Order into the small HTTP
representation required by the client.

For a missing Order, the existing error translation remains in place:

`OrderRecord.DoesNotExist` → `OrderNotFound` → `404 Not Found`

No separate read model, query repository, DTO, query bus, or CQRS abstraction
is introduced.

## Why

The existing architecture satisfies the current read requirement correctly
and with little additional complexity.

Introducing a separate read architecture merely because reads may eventually
have different needs would design for anticipated pressure rather than
observed pressure.

The current implementation does reveal a potentially important cost: the
system reconstructs a full Domain `Order` aggregate even though the HTTP
response currently needs only its identity and status.

For one Order, that cost is acceptable. It is therefore recorded as an
observation rather than treated as sufficient justification for redesign.

## Consequences

### Positive

- The first read capability remains small.
- The HTTP adapter depends on an Application capability rather than owning
  retrieval logic.
- Existing repository abstractions are reused.
- Existing error translation from the previous architectural decision is
  reused unchanged.
- No speculative read-side abstractions are introduced.

### Trade-off

Retrieving an Order for display currently requires reconstructing the Domain
aggregate, including data that the client may not need.

This may become inefficient or inconvenient when read requirements become
larger or more specialized.

That pressure has not appeared yet.

## Principle

> A read does not need a separate architecture merely because it is a read.

Use the simplest architecture that satisfies the current requirement. Let
different read needs earn different abstractions when their pressure becomes
visible.
