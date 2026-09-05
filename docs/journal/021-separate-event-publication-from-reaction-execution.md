# 021 — Separate Event Publication from Reaction Execution

## Context

NovaTrade already dispatched Domain Events only after the Order-placement
transaction completed successfully.

This protected the transaction from reaction failures, but the reactions were
still executed synchronously inside the caller's execution path.

A slow reaction therefore delayed the customer even though the Order had
already been successfully placed.

The important discovery was:

> After the transaction does not necessarily mean outside the request.

## Decision

Separate preserving, publishing, and processing Domain Events into distinct
responsibilities.

- `EventRepository.remember(event)` preserves a business fact.
- `EventPublisher.publish(event)` hands a committed business fact off for
  later processing.
- `EventDispatcher.dispatch(event)` executes the reactions interested in that
  event.

Order-placement orchestration now depends on `EventPublisher` rather than
directly invoking `EventDispatcher`.

The orchestration was consequently renamed from
`place_order_and_dispatch()` to `place_order_and_publish()`.

An `InMemoryEventPublisher` was introduced as the simplest executable adapter
for the publishing contract. It stores published events as pending work
without executing reactions.

## Consequences

Reaction execution is no longer a responsibility of Order-placement
orchestration.

A failed Unit of Work still prevents publication, preserving the existing
transactional guarantee.

The `EventDispatcher` continues to own reaction execution and its failure
semantics independently of publication.

The in-memory publisher demonstrates the semantic distinction between handing
work off and executing it, but it does not provide production asynchronous
processing.

Its pending events:

- remain inside the current Python process,
- are not durable,
- cannot be consumed independently by another application,
- disappear when the process terminates.

The real HTTP Order-placement endpoint therefore has not yet been wired to this
publisher. Creating a new in-memory publisher for each HTTP request would make
the published events inaccessible as soon as the request ends.

A durable process boundary is still missing.

## Alternatives Considered

### Continue synchronous dispatch after commit

Rejected because moving reactions outside the transaction does not remove them
from the customer's request execution.

### Make `EventDispatcher` asynchronous

Rejected because dispatching and publishing are different responsibilities.
The dispatcher should execute reactions; it should not also decide how work
crosses an execution boundary.

### Introduce Redis, RQ, Celery, threads, or asyncio immediately

Deferred because the architectural requirement is the handoff boundary, not a
specific infrastructure technology.

Infrastructure should be introduced only when another execution context needs
to receive and process the published work.

### Use `InMemoryEventPublisher` directly in the Django HTTP view

Rejected as a production solution because a publisher created for a request
would disappear with its pending events when that request ends.

## Resulting Direction

NovaTrade now distinguishes:

    business fact
         |
         v
    EventRepository
      preservation

    committed fact
         |
         v
    EventPublisher
        handoff

    received event
         |
         v
    EventDispatcher
       execution

The remaining question is no longer whether reactions should execute during
Order placement.

It is:

> What receives the published event after the current application hands it off?

That pressure requires a separate execution context and is intentionally left
for the next architectural step.
