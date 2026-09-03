# Architecture Journal 010 — Reconstituting Orders Without Replaying Business Behavior

## Context

NovaTrade can now persist Orders using Django and retrieve them later through the `DjangoOrderRepository`.

At the end of Chapter 11, reconstructing an Order from persistence was still performed by creating an Order and replaying Domain operations:

```python
order = Order(order_id=order_record.id)

for line_record in order_record.lines.all():
    order.add_product(
        product_id=line_record.product_id,
        quantity=line_record.quantity,
    )

if order_record.status == "placed":
    order.place()
```

This was acceptable while placing an Order only changed its status. Replaying `place()` happened to produce the state we needed.

A new business requirement exposed the weakness in that approach:

> When an Order is placed, NovaTrade must record when the placement happened.

The Domain therefore gained a historical business fact:

```python
order.placed_at
```

and placing an Order became:

```python
order.place(placed_at)
```

The placement time represents when the business event actually happened. It must survive persistence and retrieval unchanged.

## Problem

Loading an existing Order is not the same operation as placing an Order.

Suppose an Order is placed on September 1 and persisted with:

```text
status = PLACED
placed_at = September 1
```

When the Order is loaded on September 3, the system is not placing it again. It is reconstructing an Order whose placement already happened.

Calling:

```python
order.place(...)
```

during retrieval would therefore mix two different responsibilities:

```text
Business behavior
    Order.place(...)

Historical reconstruction
    restore an already-existing Order
```

Business methods describe operations happening now within the Domain. Persistence retrieval describes facts that already happened.

Replaying business behavior during loading becomes increasingly dangerous as business operations acquire more consequences.

## Decision

Introduce an explicit Domain reconstitution operation:

```python
Order.reconstitute(...)
```

The method restores the known historical state of an existing Order:

```python
@classmethod
def reconstitute(
    cls,
    order_id: UUID,
    status: OrderStatus,
    placed_at: datetime | None,
    lines: tuple[OrderLine, ...],
) -> "Order":
    order = cls(order_id=order_id)
    order._lines = list(lines)
    order.status = status
    order.placed_at = placed_at
    return order
```

This gives the Domain two intentionally different entry points:

```text
Order()
    → create a new Order

Order.reconstitute(...)
    → restore an existing Order
```

Business operations such as:

```python
order.add_product(...)
order.place(...)
order.confirm()
order.cancel()
```

remain responsible for performing business behavior.

`reconstitute()` does not replay those operations. It restores historical facts.

## Persistence Mapping

The Django repository remains responsible for translating between the Domain model and Django persistence models.

Writing:

```text
Order
  ↓
DjangoOrderRepository.remember()
  ↓
OrderRecord / OrderLineRecord
```

Reading:

```text
OrderRecord / OrderLineRecord
  ↓
DjangoOrderRepository.get()
  ↓
Order.reconstitute(...)
  ↓
Order
```

The repository explicitly converts persisted values back into Domain concepts such as:

```python
OrderStatus(...)
Quantity(...)
OrderLine(...)
```

Django therefore remains an adapter. The Domain does not know about `OrderRecord`, Django models, database tables, migrations, or the ORM.

## Why Reconstitution Belongs to the Domain

The persistence adapter must know how to read stored data, but it should not gain permission to manipulate an Order's internals directly.

Code such as:

```python
order._lines = ...
order.status = ...
order.placed_at = ...
```

inside the Django repository would make infrastructure responsible for constructing valid Domain state.

Instead, the Domain owns the explicit operation that restores one of its objects.

The name `reconstitute` deliberately avoids infrastructure terminology. Alternatives such as:

```text
from_database()
from_django()
from_record()
from_persistence()
```

would introduce technical persistence concepts into the Domain vocabulary.

An Order can be reconstituted from historical state regardless of where that state was stored.

## Placement Time

The Domain does not obtain the current time itself.

Instead:

```python
order.place(placed_at)
```

requires the placement time explicitly.

The Application use case therefore accepts the time and coordinates the operation:

```python
def place_order(
    order_id: UUID,
    orders: OrderRepository,
    placed_at: datetime,
) -> None:
    order = orders.get(order_id)
    order.place(placed_at)
    orders.remember(order)
```

This keeps the Domain deterministic and avoids introducing an implicit dependency on the system clock.

A Clock abstraction has not been introduced because the current requirements do not justify one.

## Persistence Change

`OrderRecord` now stores the placement time:

```python
placed_at = models.DateTimeField(null=True)
```

The field is nullable because a draft Order has not yet been placed.

`DjangoOrderRepository.remember()` persists the value, while `get()` supplies the persisted value to `Order.reconstitute()`.

The integration test verifies that an Order placed at a known time can be persisted and retrieved with the same placement time.

This protects the historical fact rather than merely reproducing the current status.

## Consequences

Loading an Order no longer performs business operations.

The distinction is now explicit:

```text
PERFORM BUSINESS                 RESTORE HISTORY

order.place(placed_at)           Order.reconstitute(...)
        │                                │
        ▼                                ▼
change Domain state              restore Domain state
        │                                │
        ▼                                ▼
status = PLACED                  identity
placed_at = supplied time        lines
                                 status
                                 placed_at
```

This prevents persistence reconstruction from accidentally triggering business behavior.

It also creates a stable place for reconstruction logic as the Domain evolves.

## Deliberately Not Introduced

This decision does not introduce:

- a Clock port,
- a mapper abstraction,
- a reconstruction service,
- repository contract tests,
- ORM-aware Domain objects,
- additional reconstitution invariants.

These concepts may become useful later, but the current pressure does not require them.

In particular, `reconstitute()` currently trusts the historical state supplied to it. Rules governing inconsistent persisted combinations, such as a `PLACED` Order without a placement time, will only be introduced when a concrete requirement makes those rules necessary.

## Principle

> Loading history is not performing business.

Business methods describe changes happening to the Domain.

Reconstitution restores the result of changes that already happened.

Keeping those two operations separate allows persistence to reconstruct the Domain without pretending that history is happening again.
