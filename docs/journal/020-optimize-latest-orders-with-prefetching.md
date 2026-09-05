# 020 — Optimize Latest Orders with Prefetching

## Context

NovaTrade's Orders overview needs the latest 100 Orders.

Chapter 21 established a correct implementation through the existing Application and repository boundaries. The Application asks for the latest Orders, while the Django persistence adapter is responsible for ordering and limiting the result in the database.

The behavior was correct, but correctness alone did not tell us how much database work was being performed.

Each persisted Order can contain Order Lines. Reconstituting an `Order` aggregate requires those lines. The Django repository first retrieved the requested `OrderRecord` rows and then, during aggregate reconstitution, accessed `order_record.lines.all()` separately for each Order.

Rather than optimizing from suspicion, we introduced an integration test that measured the number of database queries performed by `DjangoOrderRepository.latest()`.

For three Orders, the desired query shape was two database queries:

1. one query to retrieve the latest Orders;
2. one query to retrieve the Order Lines belonging to those Orders.

The existing implementation performed four queries instead:

1. one query for the Orders;
2. one query for the first Order's lines;
3. one query for the second Order's lines;
4. one query for the third Order's lines.

The number of additional queries therefore grew with the number of Orders being reconstituted. The measurement exposed an N+1 query problem.

## Decision

Optimize `DjangoOrderRepository.latest()` inside the Django persistence adapter by prefetching the related Order Lines:

```python
order_records = (
    OrderRecord.objects
    .prefetch_related("lines")
    .order_by("-created_at")[:limit]
)
```

The existing aggregate reconstitution logic remains unchanged.

Django retrieves the selected Orders with one query and their related Order Lines with a second query. When `_reconstitute()` accesses `order_record.lines.all()`, Django can use the prefetched related objects instead of issuing another query for every Order.

The integration test records this performance expectation explicitly: retrieving three latest Orders and reconstituting their lines requires two database queries rather than one additional lines query per Order.

No changes are required to the Domain model, Application use case, or `OrderRepository` port.

## Why This Decision

The measured problem belongs to the Django persistence adapter.

The Application already expresses the business requirement correctly:

> Return the latest 100 Orders.

The Domain model also remains appropriate. An `Order` aggregate contains its lines because those lines participate in Order state and business behavior.

The inefficiency originated in how the Django adapter reconstructed multiple aggregates from relational persistence. The persistence adapter is therefore the smallest boundary capable of solving the measured problem.

Changing broader architectural boundaries would solve a larger problem than the available evidence currently demonstrates.

This preserves an important distinction: a performance problem can create architectural pressure without necessarily requiring an architectural restructuring. Sometimes the existing boundary is already the correct boundary, and only its implementation needs to improve.

## Alternatives Considered

### Leave the Implementation Unchanged

Rejected.

The query-count test demonstrated that database work grew with the number of Orders being reconstituted. The result was functionally correct but unnecessarily expensive.

### Continue Loading Each Order's Lines Separately

Rejected.

This preserves the N+1 query shape and allows the number of database queries to grow with the collection size.

### Introduce a Separate Read Model or Query Service

Not introduced.

The Orders overview currently returns only a small part of each `Order`, which raises a legitimate architectural question: should this read reconstruct complete Domain aggregates at all?

However, the measured performance problem was solved locally with prefetching while preserving the existing contracts.

A separate read abstraction would therefore introduce additional architectural responsibility beyond what the demonstrated pressure currently requires.

### Introduce CQRS

Not introduced.

The existence of a read use case, a collection read, or even a performance problem does not by itself justify separating command and query responsibilities.

The current pressure can still be handled cleanly through the existing repository abstraction and its Django adapter.

CQRS should enter the architecture when the requirements of the query side become sufficiently different from aggregate-oriented command behavior that using the same model for both creates meaningful and measurable friction.

That pressure has not yet been demonstrated.

## Consequences

### Positive

- The measured N+1 query behavior is eliminated for latest-Order retrieval.
- Query count no longer grows by one additional lines query for every Order being reconstituted.
- The performance expectation is protected by an integration test.
- Domain and Application code remain independent of Django ORM optimization details.
- Existing repository contracts remain unchanged.
- Aggregate reconstitution remains centralized in the Django repository.
- No new architectural abstraction is introduced merely because a more sophisticated pattern is available.

### Trade-offs

- The collection read still reconstructs complete `Order` aggregates.
- Related Order Lines are still retrieved even though the current Orders overview returns only `id` and `status`.
- A constant number of queries does not imply a constant amount of retrieved data. Two queries can still load many rows when many Orders contain many lines.
- A future read requirement may therefore create stronger pressure for a dedicated query model or query path.

These trade-offs are accepted for now because they have not yet produced sufficient pressure to justify a broader architectural split.

## Architectural Principles

> **Measure the problem before changing the architecture.**

A suspected performance problem should first become observable. Once the cost is known, solve it at the smallest boundary capable of addressing it cleanly.

In this case, the persistence adapter could eliminate the measured N+1 behavior without changing the Application or Domain.

A second principle follows:

> **A performance problem does not automatically require an architectural pattern.**

The presence of inefficient persistence behavior does not, by itself, justify CQRS, a read model, a DTO, or a query service. Those abstractions should solve responsibilities that the existing architecture can no longer express cleanly.

Finally:

> **Sometimes the architectural decision is not to add architecture.**

After eliminating the N+1 problem, the collection read still raised an interesting question: the API currently needs only `id` and `status`, while the repository reconstructs complete `Order` aggregates. That observation is worth preserving, but an observation is not automatically architectural pressure.

We therefore stop here.

CQRS and dedicated read models remain available tools for future requirements. If NovaTrade eventually needs queries whose shape, scale, filtering, aggregation, or performance characteristics no longer fit aggregate reconstruction cleanly, that pressure can earn a separate read architecture.

Until then, the simpler architecture remains the better-supported decision.
