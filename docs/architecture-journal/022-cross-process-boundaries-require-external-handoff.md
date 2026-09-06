# 022 — Cross-Process Boundaries Require External Handoff

## Context

Chapter 23 separated publishing a Domain Event from executing the reactions interested in that event.

After an Order was successfully placed and its transaction completed, the Application could publish the resulting `OrderPlaced` event through an `EventPublisher` port instead of immediately dispatching reactions. An `InMemoryEventPublisher` gave that boundary a concrete implementation:

```
OrderPlaced
    ↓
EventPublisher
    ↓
InMemoryEventPublisher
    ↓
_pending_events
```

This solved an important responsibility problem: publishing and dispatching were no longer the same operation.

It did not, however, create an execution boundary.

The pending events still existed only in the memory of the Python process that published them. Another application process could not access that memory, and terminating the publishing process would destroy the pending events.

NovaTrade now has a stronger requirement:

> **A Domain Event published by one application process must be available to another application process without sharing Python memory.**

## Decision

Introduce Redis as external infrastructure for handing Domain Events from one application process to another.

The existing `EventPublisher` port remains the Application-facing publication boundary. A `RedisEventPublisher` adapter serializes `OrderPlaced` and places its transport representation into Redis.

On the other side of the boundary, a `RedisEventReceiver` retrieves that representation from Redis and reconstructs an `OrderPlaced` Domain Event.

```
APPLICATION A                         APPLICATION B

OrderPlaced
    │
    ▼
EventPublisher
    │
    ▼
RedisEventPublisher
    │
    ▼
════════════════════════════════════════
              Redis
         novatrade:events
════════════════════════════════════════
                                      │
                                      ▼
                            RedisEventReceiver
                                      │
                                      ▼
                                 OrderPlaced
```

The applications therefore communicate through external infrastructure rather than through shared Python objects.

## Why Redis

The new pressure requires a mechanism whose state exists outside either Python process.

Redis provides the smallest external infrastructure boundary currently required by NovaTrade. One process can publish data and another independent process can retrieve it without introducing a worker framework or coupling publication to a particular reaction.

Redis is therefore introduced here as **transport infrastructure**.

It is not an email sender, a fulfillment processor, or a background-job framework. Those are different responsibilities and should not be collapsed into the transport simply because Redis is involved.

## Serialization Is Part of the Boundary

A Python `OrderPlaced` object cannot literally move from one process to another.

The publishing adapter must first convert the Domain Event into transportable data:

```text
OrderPlaced
    ↓
serialization
    ↓
Redis representation
```

The receiving adapter performs the inverse transformation:

```text
Redis representation
    ↓
deserialization
    ↓
OrderPlaced
```

The transport representation therefore remains an infrastructure concern. Once the data reaches the receiving side, the application can again reason in terms of the Domain Event rather than Redis-specific structures.

At this stage, NovaTrade has only one Domain Event crossing this boundary. Introducing a generic event hierarchy, serializer abstraction, event registry, or event envelope would solve a problem the system does not yet have.

## Testing Strategy

The Redis boundary is tested at two different levels.

Focused adapter tests use `fakeredis`. They verify that publication places the event representation outside the publisher object and that the receiving adapter can reconstruct the original `OrderPlaced` event. These tests remain fast and do not depend on external infrastructure.

However, `fakeredis` executes inside the same Python process as the test. It can prove adapter behavior, but it cannot prove execution separation.

A separate integration test therefore uses the real Redis instance running through Docker and launches independent Python subprocesses:

```
Python Process A
       │
       ▼
RedisEventPublisher
       │
       ▼
    Redis
       │
       ▼
RedisEventReceiver
       │
       ▼
Python Process B
```

Process B has no access to Process A's Python memory. Their shared communication boundary is Redis.

The integration test therefore proves the architectural property that motivated this decision rather than merely reproducing Redis-like behavior inside one process.

## TDD Progression

### 1. Publishing Must Leave Publisher Memory

The first test required a published event to be stored outside the publisher rather than in an internal collection owned by that object.

The genuine RED occurred because `RedisEventPublisher` did not exist.

The smallest GREEN introduced a Redis publisher that serialized `OrderPlaced` and pushed its representation to the shared event channel.

This changed the ownership of pending work:

```
Before

InMemoryEventPublisher
    ↓
_pending_events


After

RedisEventPublisher
    ↓
Redis
```

### 2. Another Side Must Recover the Business Fact

Moving data outside the publishing process was not sufficient. Another execution needed to recover the business fact in a form the application understood.

The second test required a `RedisEventReceiver` capable of reconstructing the original `OrderPlaced`.

The genuine RED occurred because the receiving adapter did not exist.

The smallest GREEN introduced a receiver that retrieved the serialized representation and reconstructed the Domain Event.

The transport representation could now cross the infrastructure boundary without leaking into the application's domain language.

### 3. The Boundary Must Work Between Processes

The first two tests used `fakeredis`. Although they proved the behavior of the adapters, both adapters still executed inside the same Python process.

That was not enough to prove the requirement of this chapter.

The third test therefore required one Python process to publish the event and another Python process to receive it through a real Redis instance.

The first attempt failed because Redis was not reachable on `localhost:6379`. That was an infrastructure problem, not a TDD RED, and was therefore not treated as evidence of missing application behavior.

After Redis connectivity was verified, the genuine RED occurred because the independently executable publishing side required by the test did not yet exist.

Small test-support executables were then introduced. One process published the event through `RedisEventPublisher`; another process retrieved it through `RedisEventReceiver`.

The integration test passed only when the event successfully crossed real Redis between independent Python executions.

## Refactoring

The publisher and receiver both depended on the same Redis channel:

```
novatrade:events
```

The integration test also needed to identify that channel in order to clean its external state before execution.

Because this name represents one shared infrastructure concept, allowing each participant to define it independently would create an unnecessary opportunity for them to drift apart.

The channel name was therefore extracted into the shared `EVENT_CHANNEL` constant.

No broader Redis abstraction was introduced.

## Consequences

NovaTrade can now hand an `OrderPlaced` event across a real process boundary.

The publishing process no longer needs the receiving side to share its Python memory. A receiving process can recover the business fact through external infrastructure and reconstruct the corresponding Domain Event.

The architecture now makes four responsibilities explicit:

```
EventRepository.remember(event)
    = preserve the business fact transactionally

EventPublisher.publish(event)
    = hand the committed business fact off

EventReceiver.receive()
    = bring the business fact into another execution

EventDispatcher.dispatch(event)
    = execute the reactions interested in the business fact
```

These responsibilities may participate in the same overall workflow, but they are not interchangeable.

Preservation is not publication.

Publication is not reception.

Reception is not reaction execution.

Crossing the process boundary also introduces costs that did not exist with an in-memory implementation. Events must be serialized. External infrastructure must be available. Communication can now fail independently of either application process.

Those costs are accepted because the requirement now demands independent execution.

## Deferred Decisions

This decision deliberately does not introduce:

- RQ
- Celery
- a long-running worker
- email-specific queue jobs
- fulfillment-specific queue jobs
- retry policies
- dead-letter handling
- a generic Domain Event hierarchy
- a generic serialization framework
- an event registry

The current requirement is to establish and prove the cross-process handoff.

How a receiving application should continuously consume events, decide which reactions to execute, and handle failures during that processing remains a separate architectural problem.

## Principles

> **Dependency separation is not execution separation.**

And once execution crosses a process boundary:

> **Serialization is the price of crossing that boundary.**
