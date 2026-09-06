# Architecture Journal 024 — Historical Data Belongs Somewhere

## Context

NovaTrade already preserves the `OrderPlaced` Domain Event when an Order is successfully placed.

The write path was established earlier:

```text
Order.place()
    ↓
OrderPlaced
    ↓
EventRepository.remember()
    ↓
DjangoEventRepository
    ↓
OrderPlacedRecord
    ↓
Database
```

This persistence exists because the business fact must survive the operation that produced it.

A new requirement introduced a different question:

> The Application must be able to retrieve the recorded Order placement history without loading Order aggregates.

The historical data was therefore not missing. What was missing was an Application-level way to read it.

## Pressure

The existing `EventRepository` exposes only:

```python
remember(event)
```

Its responsibility is to preserve Domain Events produced during a business operation.

One possible response would have been to extend it:

```python
remember(event)
list()
```

That would be convenient, but it would combine two different responsibilities.

The command side needs to preserve a business fact as part of a transactional operation. The historical query needs to retrieve information for inspection without reconstructing an `Order` or performing business behavior.

The existing `OrderRepository` was also unsuitable for this query. Its read operations return `Order` aggregates. Loading those aggregates merely to answer which Orders were placed and when would make the query depend on a model it does not need.

## Decision

Introduce a dedicated Application port for historical placement queries:

```text
OrderPlacementHistory
```

and an Application query:

```text
list_order_placement_history()
```

The Django adapter implements that port directly from the existing historical records:

```text
OrderPlacedRecord
        ↓
DjangoOrderPlacementHistory
        ↓
OrderPlacementHistory
        ↓
list_order_placement_history()
```

The query currently returns only the information required:

```text
(order_id, placed_at)
```

It does not reconstruct `Order` aggregates and does not expose Django models to the Application.

The existing `EventRepository` remains focused on preserving events. No `list()` method was added to it.

## Why This Creates Pressure for CQRS

Until now, NovaTrade's queries could still naturally use the same model that supports business behavior.

`get_order()`, `list_orders()`, and `latest()` return `Order` aggregates. Even when those reads created performance pressure, they still wanted the same conceptual model.

Historical placement information is different.

The write path begins with the business model:

```text
Order
    ↓
place()
    ↓
OrderPlaced
    ↓
EventRepository
```

The historical read path does not need an `Order` aggregate:

```text
OrderPlacedRecord
    ↓
OrderPlacementHistory
    ↓
(order_id, placed_at)
```

For the first time, NovaTrade has a concrete requirement where forcing the query through the existing domain-oriented repository would work against the problem being solved.

This creates genuine pressure for **Command Query Responsibility Segregation (CQRS)**.

CQRS has **not** been explicitly implemented in this chapter.

There are no Commands, Command Handlers, Queries, Query Handlers, command buses, or query buses yet.

Instead, Chapter 26 establishes the architectural reason those concepts may become useful: changing business state and answering historical questions are beginning to require different paths.

## Why CQRS Was Not Introduced Earlier

Chapter 22 exposed read-performance pressure.

At that point, the query still wanted `Order` aggregates. Optimizing the Django repository's database access solved the performance problem without requiring a different Application model.

Introducing CQRS there would therefore have been speculative.

Chapter 26 changes the situation.

The Application now needs historical information that can be retrieved directly from recorded business facts without reconstructing the aggregate that originally produced them.

The important discovery is therefore not:

> NovaTrade now uses CQRS.

It is:

> NovaTrade has reached the kind of pressure that can justify CQRS.

The distinction matters because the architecture should continue to emerge from requirements rather than from a predetermined pattern catalogue.

## Alternatives Rejected

### Add `list()` to `EventRepository`

Rejected because `EventRepository` exists to preserve Domain Events during business operations. Historical querying has a different purpose.

Adding read behavior merely because the same persistence table is involved would make the abstraction follow storage convenience rather than Application responsibility.

### Use `OrderRepository`

Rejected because the historical query does not require `Order` aggregates.

Reconstructing them would introduce unnecessary domain work and couple a historical query to a model designed primarily around business behavior.

### Return `OrderPlacedRecord`

Rejected because `OrderPlacedRecord` is a Django persistence model.

Returning it would allow the framework adapter to leak into the Application boundary.

### Introduce a Dedicated Read-Model Class

Not introduced yet.

A type such as:

```text
OrderPlacementHistoryEntry
```

could eventually make the result more expressive, but the current requirement only needs an Order identity and placement timestamp.

There is not yet enough pressure to justify another abstraction.

### Introduce CQRS Immediately

Rejected for this chapter.

Although the new historical query exposes the pressure that motivates CQRS, introducing Commands, Queries, Handlers, buses, and other CQRS structures in the same step would move ahead of the requirement.

Chapter 26 preserves the discovery. Explicit CQRS can follow once that separation is deliberately addressed.

## Result

NovaTrade now has two emerging paths around the same historical data:

```text
                 NovaTrade

        BUSINESS / WRITE PATH
                 │
              Order
                 │
             place()
                 │
           OrderPlaced
                 │
          EventRepository
                 │
      DjangoEventRepository
                 │
                 ▼
        OrderPlacedRecord
                 ▲
                 │
    DjangoOrderPlacementHistory
                 │
       OrderPlacementHistory
                 │
    list_order_placement_history
                 │
                 ▼
       HISTORICAL READ PATH
```

The write path preserves a business fact.

The read path retrieves historical information.

They may share persistence, but they no longer need to share an Application abstraction merely because the data lives in the same place.

This asymmetry is now visible enough to motivate the next architectural question:

> If commands and queries increasingly need different paths, should NovaTrade make that separation explicit?

## TDD Evidence

### RED 1 — The Application Cannot Ask for History

Requirement:

> The Application must be able to retrieve the recorded Order placement history without loading Order aggregates.

The first test failed because the Application query did not exist:

```text
ModuleNotFoundError:
No module named 'novatrade.application.list_order_placement_history'

1 error in 0.47s
```

### GREEN 1 — Introduce the Historical Query Boundary

Introduced:

```text
OrderPlacementHistory
list_order_placement_history()
```

Result:

```text
1 passed in 0.06s
```

### RED 2 — Django Cannot Answer the Query

The Application now had a historical-query abstraction, but the Django adapter could not implement it.

The integration test failed with:

```text
ModuleNotFoundError:
No module named
'novatrade.adapters.django.order_app.persistence.order_placement_history'

1 error in 0.50s
```

### GREEN 2 — Read Existing Historical Records

Introduced:

```text
DjangoOrderPlacementHistory
```

which reads directly from the existing `OrderPlacedRecord` persistence model.

Result:

```text
1 passed in 0.42s
```

### Chapter Slice

```text
2 passed in 0.48s
```

### Full Regression Suite

```text
91 passed in 2.00s
```

## Architectural Principle

> **Historical data should be read according to the questions the business asks, not according to the model that originally produced it.**

And the pressure revealed by this chapter:

> **When changing state and answering questions begin to want different models or paths, forcing both responsibilities through the same abstraction becomes a reason to consider CQRS.**

## Status

**Accepted.**

Chapter 26 introduces a dedicated historical read path and establishes genuine pressure for CQRS.

CQRS itself has not yet been explicitly introduced. Commands, Queries, and their Handlers remain a subsequent architectural decision.
