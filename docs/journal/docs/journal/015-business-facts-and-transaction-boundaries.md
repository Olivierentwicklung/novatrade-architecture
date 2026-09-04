# Architecture Journal 015 — Business Facts and Transaction Boundaries

## Context

NovaTrade's `Order` can produce an `OrderPlaced` Domain Event when it is successfully placed. The Domain records this event because placing an Order is not merely a change of internal state; it is a business fact that other parts of the system may care about.

The Application can dispatch that fact to multiple reactions. At this stage, a placed Order may trigger customer confirmation and fulfillment notification.

This introduced a failure problem that did not exist while Domain Events remained only inside the aggregate: the Order is persisted transactionally, but external reactions can fail independently.

## Pressure

Dispatching an `OrderPlaced` event before the Order transaction commits is unsafe.

A reaction could succeed while persistence subsequently fails:

```text
BEGIN TRANSACTION
      │
      ├── place Order
      ├── persist Order
      ├── produce OrderPlaced
      ├── dispatch OrderPlaced
      │       └── external reaction succeeds
      │
      ├── commit fails
      │
      ▼
   ROLLBACK
```

The external world would have reacted to a business fact that never became true in persisted state.

Dispatching only after the Unit of Work succeeds avoids that inconsistency, but exposes another failure mode:

```text
Order committed
      │
      ▼
OrderPlaced
      │
      ▼
dispatcher
   │
   ├── reaction A succeeds
   │
   └── reaction B fails
```

At this point the database transaction cannot simply be rolled back. The Order has already been committed, and reaction A may already have produced an external side effect.

Retrying the complete dispatch could execute reaction A twice. Ignoring the failure could permanently lose reaction B.

The system therefore needs the business fact itself to survive independently of the immediate reactions that consume it.

## Decision

Business facts produced by an Application operation and required beyond that operation are persisted through the same Unit of Work as the aggregate state that makes those facts true.

The Unit of Work therefore exposes two persistence capabilities:

```text
UnitOfWork
├── orders
└── events
```

When an Order is placed, the Application performs the operation inside one Unit of Work:

```text
place_order()
      │
      ├── load Order
      ├── Order.place()
      ├── persist Order
      ├── collect OrderPlaced
      └── persist OrderPlaced
              │
              ▼
       same transaction
```

The Django adapter implements both persistence operations inside the same `transaction.atomic()` boundary.

Consequently:

```text
COMMIT
├── Order state survives
└── OrderPlaced fact survives

ROLLBACK
├── Order state disappears
└── OrderPlaced fact disappears
```

The Domain does not persist its own events. The `Order` continues only to record what happened. Persistence remains an Application and infrastructure concern.

The Order repository also remains responsible only for Order state. It does not inspect or consume pending Domain Events.

The Application explicitly collects the produced events and asks the event persistence Port to preserve them.

## Why the Event Is Persisted Before Dispatch

The durable event is written while the Unit of Work is active, but it is returned to the caller only after the Unit of Work exits successfully.

This establishes an important ordering:

```text
produce fact
     │
     ▼
persist state + fact
     │
     ▼
commit
     │
     ▼
return fact
     │
     ▼
dispatch reactions
```

A failed transaction therefore prevents dispatch of a fact that did not successfully become durable.

External reactions remain outside the transaction.

This does not make reaction delivery atomic with the database transaction. Instead, it deliberately separates two different problems:

1. transactional consistency of business state and business facts;
2. reliable delivery of those facts to interested reactions.

Chapter 17 addresses the first problem.

## Alternatives Considered

### Dispatch Before Commit

Rejected.

An external reaction could succeed before the database transaction fails. NovaTrade would then have produced consequences for an Order placement that does not exist in committed state.

### Put External Reactions Inside the Database Transaction

Rejected.

A database transaction cannot reliably roll back arbitrary external effects such as sending a confirmation or notifying another system. It would also make transaction duration and success depend on external collaborators.

### Roll Back the Order When a Reaction Fails

Rejected.

Reactions happen after the Order transaction has successfully completed. At that point, the Order placement is already a committed business fact. A later failure does not make the original placement untrue.

### Retry the Entire Dispatch Immediately

Not introduced.

If one reaction succeeds and a later reaction fails, retrying all reactions could repeat already successful external effects.

Reliable retries require additional semantics that the current system does not yet possess.

### Ignore Reaction Failures

Rejected.

Ignoring the failure would make the system appear successful while silently losing a required business consequence.

### Let the Order Repository Persist Domain Events

Rejected.

The Order repository is responsible for preserving and reconstituting Order state. Making it inspect and consume pending Domain Events would mix aggregate persistence with event persistence and hide an Application-level decision inside an infrastructure adapter.

### Introduce a Full Transactional Outbox

Not introduced yet.

NovaTrade now has a durable representation of `OrderPlaced` written in the same transaction as the Order state. This provides an important prerequisite for reliable delivery, but the system does not yet have a delivery lifecycle.

There is currently no concept of pending delivery, processing state, retries, workers, or recovery of unprocessed events.

Naming and implementing a complete Outbox mechanism now would introduce a solution before those pressures exist.

## Consequences

The Application's Unit of Work now includes both Order persistence and Domain Event persistence.

A successful Order placement guarantees that the persisted Order state and its durable `OrderPlaced` fact agree.

A failed transaction guarantees that neither survives.

Domain Events remain business facts produced by the Domain rather than infrastructure messages.

External reactions occur only after successful completion of the business transaction.

Reaction failures can still produce partial delivery. That limitation is now explicit rather than hidden.

The durable event provides a future recovery point, but NovaTrade does not yet implement the mechanism that would perform that recovery.

The repository structure was also refactored after these responsibilities became clear. Application reactions now have an explicit `application/reactions/` location, while Django persistence distinguishes `order_repository.py` from `event_repository.py`. The refactor introduced no behavioral change and remained protected by the existing test suite.

## What We Are Not Introducing

At this stage NovaTrade does not introduce:

- asynchronous workers;
- message queues;
- retry policies;
- processed-event markers;
- generic event envelopes;
- generic Domain Event base classes;
- delivery acknowledgements;
- idempotency mechanisms;
- a generic message bus;
- a complete Transactional Outbox implementation.

Those concepts require additional operational pressure.

## Principle

> **The state change and the durable business fact live or die in the same transaction.**
