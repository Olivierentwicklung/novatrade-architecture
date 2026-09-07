# 027 — All the Pieces Work. Does the System?

## Context

By the end of Chapter 28, NovaTrade had accumulated an architecture one requirement at a time.

The Domain protected the business rules around Orders. Application use cases coordinated business operations. Repositories separated persistence from the Domain. A Unit of Work defined transaction boundaries. Domain Events represented business facts. Redis transported those facts across a process boundary. An Event Receiver brought them into another execution context. An Event Dispatcher connected events to interested Application reactions. Commands and Queries had begun to use different models. Finally, Composition Roots assembled concrete infrastructure at the application's edge.

Every individual piece had tests.

That created a new kind of uncertainty.

The question was no longer whether the individual parts worked.

The question was:

> **All the pieces work. Does the system?**

A collection of well-tested components is not automatically a working system. Unit tests can prove behavior in isolation. Integration tests can prove that selected technologies cooperate. Even architectural boundaries can look correct when inspected independently.

At some point, the complete business journey has to be exercised.

---

## First System-Level Requirement

We started with a concrete journey:

> **When a customer places an Order through the HTTP API, the resulting `OrderPlaced` event must cross the process boundary and be available to the processing application.**

This was deliberately larger than the tests that already existed.

The HTTP E2E tests proved:

```text
HTTP
→ Application
→ Domain
→ Database
→ persisted OrderPlaced
```

The Redis integration test separately proved:

```text
manually constructed OrderPlaced
→ RedisEventPublisher
→ real Redis
→ RedisEventReceiver
```

Both were useful.

Neither proved that an event produced by a real HTTP business operation actually reached Redis.

There was a gap between two independently tested islands.

---

## The Expected RED That Never Happened

We wrote a system-level E2E test that:

1. created an Order,
2. persisted it,
3. placed it through the real HTTP API,
4. read the next event from real Redis,
5. verified that the received `OrderPlaced` belonged to the Order that had just been placed.

The test crossed:

```text
HTTP
→ Django
→ PlaceOrderCommandHandler
→ Domain
→ transaction
→ RedisEventPublisher
→ real Redis
→ RedisEventReceiver
```

We expected this larger test might expose a missing connection.

Instead:

```text
1 passed
```

The test was green immediately.

This was not a TDD RED and must not be rewritten as one.

The immediate GREEN was evidence.

The architecture that had emerged during the previous chapters was already capable of carrying a real business fact from the HTTP boundary across Redis to the receiving side.

No production change was necessary.

---

## An Immediate GREEN Can Still Teach Us Something

TDD does not require pretending that every new test fails.

Sometimes a test expresses behavior that the existing architecture already supports.

That tells us something valuable:

> **The architecture composed better than our isolated tests had previously demonstrated.**

The correct response was not to manufacture a failure.

It was to accept the evidence and ask a larger question.

Receiving the event from Redis proved that the fact crossed the process boundary.

But NovaTrade did not publish `OrderPlaced` merely so another process could deserialize it.

Something was supposed to happen because the Order had been placed.

---

## Following the Processing Side

The Application already contained:

```text
process_next_event
```

It knew how to ask an `EventReceiver` for the next event and pass that event to an `EventDispatcher`.

The dispatcher already knew that `OrderPlaced` interested two reactions:

```text
OrderPlaced
    │
    ├── send_order_confirmation
    │
    └── notify_fulfillment
```

Those reactions depended on two outbound ports:

```text
OrderConfirmationSender

FulfillmentNotifier
```

Application-level tests already proved this behavior using test doubles. The existing processing test uses a stub receiver together with spy implementations of those two outbound ports, builds the dispatcher, processes the event, and verifies that both reactions receive the event's Order identity and placement time.

So the processing logic existed.

The question became whether the processing application itself could actually be assembled.

---

## Inspect Before Designing

Before introducing another abstraction, we inspected the repository.

The adapter landscape contained:

- Django HTTP adapters,
- Django persistence adapters,
- in-memory adapters,
- `RedisEventPublisher`,
- `RedisEventReceiver`.

But there were no production implementations of:

```text
OrderConfirmationSender
FulfillmentNotifier
```

There was also no production processing entry point assembling:

```text
RedisEventReceiver
+
EventDispatcher
+
process_next_event
```

This distinction mattered.

It would have been easy to conclude:

> We need an email adapter and a fulfillment HTTP client.

But no requirement had told us that confirmation must use SMTP, an email provider, or even email at all. Likewise, nothing had established that fulfillment was another HTTP service.

Choosing those technologies would have been architecture by imagination rather than architecture by pressure.

The principle remained:

> **No pattern without pressure.**

And here it led to a closely related rule:

> **No infrastructure without a requirement.**

---

## The Actual Missing Capability

The system did not need another Domain concept.

It did not need another Application abstraction.

It did not need a generic message bus.

It needed an executable boundary that could connect infrastructure already present in the repository to Application behavior already present in the repository.

The missing capability was:

> **Process the next published Domain Event using the configured Application reactions.**

That gave us a second system-level test.

This time the journey was larger:

```text
HTTP
→ Django
→ Application
→ Domain
→ Redis
→ processing application
→ EventDispatcher
→ confirmation boundary
→ fulfillment boundary
```

The test used real Django, the real Domain, the real write-side composition, real Redis, and the real processing Application behavior.

Only the final unspecified external systems were represented by spies.

That was intentional.

The test was proving that NovaTrade reached its outbound architectural boundaries. It was not pretending that an email provider or fulfillment service had already been specified.

---

## RED — The Processing Application Cannot Be Entered

The new system test asked for:

```python
process_next_published_event(...)
```

from:

```text
novatrade.bootstrap.process_events
```

The test failed during collection:

```text
ModuleNotFoundError:
No module named 'novatrade.bootstrap.process_events'
```

This was a genuine RED.

Unlike the first system test, the repository inspection had already established that the requested production boundary did not exist.

The failure represented an actual architectural gap:

```text
RedisEventReceiver                         ✓
process_next_event                         ✓
EventDispatcher                            ✓
Application reactions                      ✓
outbound ports                             ✓

production processing composition          ✗
```

The individual pieces worked.

There was simply no production entry point connecting them.

---

## GREEN — Assemble What Already Exists

The smallest implementation introduced:

```text
src/novatrade/bootstrap/process_events.py
```

with a single production function:

```python
process_next_published_event(...)
```

Its responsibility was composition.

Conceptually:

```text
process_next_published_event
        │
        ├── RedisEventReceiver
        │
        ├── build_event_dispatcher
        │
        └── process_next_event
```

The function created the concrete Redis receiver, built the dispatcher using the supplied outbound adapters, and delegated processing to the existing Application function.

No new business logic was introduced.

No existing Application behavior was duplicated.

No new architectural layer was invented.

The system-level test became green:

```text
1 passed
```

The full regression suite then confirmed:

```text
99 passed in 2.25s
```

---

## Why the Outbound Adapters Remain Supplied

`process_next_published_event()` receives implementations of:

```text
OrderConfirmationSender
FulfillmentNotifier
```

rather than constructing concrete production technologies itself.

That is not unfinished dependency injection for its own sake.

NovaTrade has not yet provided enough information to choose those technologies.

The architecture currently knows the capabilities it requires:

```text
send confirmation

notify fulfillment
```

It does not yet know whether those capabilities will eventually be fulfilled by:

```text
SMTP
email provider
HTTP API
message queue
another process
some other technology
```

The ports preserve that distinction.

The system test therefore uses spies at precisely those unresolved external boundaries.

This allows the test to prove the architecture's current claim without pretending to prove infrastructure that does not exist.

---

## What We Deliberately Did Not Build

The successful system test creates several tempting next steps.

We could introduce a continuously running worker:

```python
while True:
    process_next_published_event(...)
```

We could add Celery or RQ.

We could implement SMTP.

We could invent a fulfillment HTTP service.

We could add retries, acknowledgements, dead-letter queues, scheduling, worker lifecycle management, graceful shutdown, monitoring, or generic message-processing abstractions.

We did none of those things.

Each introduces new architectural questions that the current requirement does not ask us to solve.

A worker loop, for example, immediately raises questions about:

- polling behavior,
- shutdown,
- failure recovery,
- retry semantics,
- poison messages,
- acknowledgement,
- observability,
- process lifecycle.

Those are legitimate concerns when the system creates the pressure for them.

They are not free improvements.

---

## Architectural Result

Before Chapter 29, NovaTrade had several independently proven architectural paths:

```text
ISLAND 1

HTTP
→ Application
→ Domain
→ Database
→ persisted Domain Event
```

```text
ISLAND 2

Domain Event
→ RedisEventPublisher
→ real Redis
→ RedisEventReceiver
```

```text
ISLAND 3

EventReceiver
→ process_next_event
→ EventDispatcher
→ Application reactions
```

Chapter 29 connected those islands.

The system can now prove a journey shaped like:

```text
                    PROCESS A

HTTP POST
    │
    ▼
Django
    │
    ▼
PlaceOrderCommandHandler
    │
    ▼
Domain
    │
    ▼
OrderPlaced
    │
    ├──────────────► persistence
    │
    ▼
RedisEventPublisher
    │
    ▼
                 REAL REDIS
═════════════════════╪════════════════════
                     │
                     ▼
               PROCESSING SIDE
                     │
                     ▼
       process_next_published_event
                     │
                     ▼
           RedisEventReceiver
                     │
                     ▼
           process_next_event
                     │
                     ▼
             EventDispatcher
                ┌────┴────┐
                ▼         ▼
          confirmation  fulfillment
                │         │
                ▼         ▼
             outbound   outbound
               port       port
```

The final two external technologies remain intentionally unspecified.

---

## Decision

Introduce a small processing-side Composition Root that connects the concrete Redis receiver to the existing Application event-processing behavior.

Do not introduce concrete confirmation or fulfillment infrastructure until requirements establish what those external systems actually are.

Do not introduce a worker framework or processing loop until execution-lifecycle pressure requires one.

---

## Consequences

### Positive

- A real business operation is now tested across multiple architectural boundaries.
- Real Redis participates in the system-level proof.
- The processing side has an explicit production composition boundary.
- Existing Application behavior remains framework- and infrastructure-independent.
- Unspecified external systems remain behind ports.
- No unnecessary processing framework was introduced.
- The full test suite remains green.

### Trade-offs

- The system test does not prove a real confirmation provider.
- The system test does not prove a real fulfillment integration.
- Processing still occurs one event at a time when explicitly invoked.
- There is no continuously running production worker.
- Redis transport semantics remain intentionally simple.

These are known boundaries of the current architecture, not hidden claims.

---

## What We Learned

A system can contain individually correct components without having proved that they form a working business journey.

System-level tests expose the spaces between architectural pieces.

But they can reveal two different things.

Sometimes the supposedly missing connection already works:

> **An immediate GREEN is evidence, not a failed TDD exercise.**

Sometimes the larger journey reveals a genuine gap:

> **The missing architecture may be composition rather than another abstraction.**

Chapter 29 demonstrated both.

The first system test showed that previously developed components already cooperated across the HTTP-to-Redis path.

The second exposed the missing processing-side entry point.

The response to that pressure was deliberately small.

> **Sometimes the next architectural step is not another pattern. It is proving—and, where necessary, completing—the path through the patterns that already earned their place.**

---

## Current Principle

> **No pattern without pressure. No infrastructure without a requirement. And no architectural claim without proof.**
