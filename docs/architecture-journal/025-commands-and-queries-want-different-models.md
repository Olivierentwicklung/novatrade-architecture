# Commands and Queries Want Different Models

## Context

NovaTrade already had Application use cases for changing business state and retrieving information. Placing an Order loaded an `Order` aggregate, executed Domain behavior, preserved the changed aggregate and its Domain Events inside a Unit of Work, and could publish those events after the transaction completed. Historical Order placement data, introduced in Chapter 26, followed a different path: the Application could retrieve recorded `OrderPlaced` facts directly through `OrderPlacementHistory` without reconstructing `Order` aggregates.

At that point, reads and writes were already structurally different, but that difference was still implicit in the Application vocabulary. `place_order()` accepted separate values such as `order_id` and `placed_at`, while `list_order_placement_history()` represented a read operation only as a function call. NovaTrade had reached the pressure for CQRS, but it had not yet introduced explicit Commands, Queries, or their Handlers.

## Pressure

The Application needed a clearer way to express the difference between an intention to change business state and a request to retrieve information.

For the write side, `order_id` and `placed_at` together represented one intention:

> Place this Order at this time.

For the read side, the request was different:

> Return the recorded Order placement history.

Treating both merely as function calls hid an architectural distinction that had become meaningful. The write path required Domain behavior, a Unit of Work, persistence, Domain Event preservation, and event publication. The historical read path required none of those things; it could use a dedicated read-oriented port.

The architecture now had enough pressure to make that distinction explicit.

## Decision

NovaTrade introduces explicit CQRS vocabulary at the Application boundary.

The write request is represented by:

```text
PlaceOrderCommand
```

and executed by:

```text
PlaceOrderCommandHandler
```

The read request is represented by:

```text
OrderPlacementHistoryQuery
```

and executed by:

```text
OrderPlacementHistoryQueryHandler
```

`PlaceOrderCommand` contains only the information describing the business intention:

```text
order_id
placed_at
```

It does not contain infrastructure such as a Unit of Work, repository, event publisher, Django object, or Redis client. Those are execution dependencies and therefore belong to the handler.

`PlaceOrderCommandHandler` delegates to the already-proven `place_order_and_publish()` Application behavior. CQRS therefore emerges around existing behavior instead of replacing or duplicating it.

The query side follows the same principle. `OrderPlacementHistoryQuery` represents the request for historical placement information. It currently has no parameters because NovaTrade has not yet required filtering, pagination, date ranges, or other query criteria.

`OrderPlacementHistoryQueryHandler` depends on the existing `OrderPlacementHistory` read port and delegates to `list_order_placement_history()`. It therefore preserves the read path established in Chapter 26.

The resulting Application structure is:

```text
COMMAND SIDE                         QUERY SIDE

PlaceOrderCommand                    OrderPlacementHistoryQuery
        │                                      │
        ▼                                      ▼
PlaceOrderCommandHandler             OrderPlacementHistoryQueryHandler
        │                                      │
        ▼                                      ▼
place_order_and_publish()            list_order_placement_history()
        │                                      │
        ▼                                      ▼
place_order()                        OrderPlacementHistory
        │                                      │
        ▼                                      ▼
Order aggregate                      historical records
```

## Why CQRS Is Earned Here

CQRS was not introduced merely because NovaTrade both reads and writes data. Every useful application does that.

Earlier read requirements did not justify explicit CQRS. In Chapter 22, NovaTrade needed to retrieve Orders efficiently, but the read side still wanted `Order` aggregates. The performance problem could be solved inside the existing repository abstraction without introducing a separate Application vocabulary.

Chapter 26 changed the pressure. Historical placement information did not need an `Order` aggregate at all. It needed recorded business facts. A dedicated read port emerged naturally, creating a meaningful structural difference between the write model and the historical read model.

Chapter 27 makes that difference explicit.

The Command side represents intentions that may change business state. The Query side represents requests for information. Their handlers depend on different collaborators because the operations themselves have different needs.

This is the point at which CQRS becomes useful rather than decorative.

## Why Existing Behavior Was Reused

The existing `place_order()` and `place_order_and_publish()` functions already encode behavior established and tested in earlier chapters. Introducing CQRS did not invalidate that work.

Instead of moving their logic immediately into `PlaceOrderCommandHandler`, the handler delegates to the existing Application behavior. Similarly, `OrderPlacementHistoryQueryHandler` delegates to the existing historical read use case.

This keeps the architectural change small and preserves previously proven semantics.

The new CQRS types provide an explicit Application interface around behavior NovaTrade already trusts.

## Why There Is No CommandBus or QueryBus

NovaTrade currently has one explicit Command and one explicit Query. Their handlers can be invoked directly.

A `CommandBus` or `QueryBus` would introduce routing and dispatch infrastructure without solving a current problem. Generic `Command` and `Query` base classes would likewise add abstraction without providing useful behavior.

They are therefore deliberately omitted.

If NovaTrade later accumulates enough Commands and Queries that selecting, registering, decorating, or dispatching handlers becomes a recurring problem, a bus may become justified. That pressure does not exist yet.

## Why the Query Has No Parameters

`OrderPlacementHistoryQuery` currently carries no data.

That is intentional.

The current business requirement asks only for recorded Order placement history. NovaTrade has not requested a limit, date range, customer filter, pagination strategy, or sort direction.

Adding such fields now would model hypothetical requirements rather than existing ones.

The Query gives the request a name without pretending that requirements exist which the business has never expressed.

## Framework Boundary Discovered

After introducing the explicit CQRS interface, source inspection revealed that the Django `PlaceOrderView` still calls `place_order()` directly.

The current real HTTP path therefore remains:

```text
HTTP
 │
 ▼
PlaceOrderView
 │
 ▼
place_order()
```

rather than:

```text
HTTP
 │
 ▼
PlaceOrderView
 │
 ▼
PlaceOrderCommand
 │
 ▼
PlaceOrderCommandHandler
```

This does not invalidate the CQRS Application interface, but it limits what can currently be claimed about the running system.

NovaTrade now has explicit Commands, Queries, and their Handlers. However, not every external entry point is yet wired through that interface.

## Why the Django View Was Not Rewired Yet

`PlaceOrderCommandHandler` requires both a `UnitOfWork` and an `EventPublisher`.

NovaTrade already has `DjangoUnitOfWork` and a production-style `RedisEventPublisher`, but source inspection showed that `RedisEventPublisher` is currently instantiated only in tests and test-support code. There is no production composition location that constructs the Redis client and wires the publisher into Application handlers.

Constructing Redis directly inside `PlaceOrderView` would make the HTTP adapter responsible for infrastructure composition:

```text
HTTP translation
+
Redis configuration
+
dependency construction
+
Application invocation
```

That would solve one boundary by weakening another.

The missing wiring therefore exposes a separate architectural pressure:

> Who constructs the concrete dependencies required by Application handlers?

That is a composition/bootstrap concern and is not solved merely because CQRS has been introduced.

Chapter 27 deliberately stops before that separate decision.

## Alternatives Rejected

### Keep using only functions

NovaTrade could continue using `place_order()` and `list_order_placement_history()` directly.

This would preserve working behavior, but the increasingly meaningful difference between state-changing requests and informational requests would remain implicit.

Rejected because the architecture has now earned explicit Application vocabulary.

### Move all existing logic into the Handlers immediately

The logic from `place_order()`, `place_order_and_publish()`, and `list_order_placement_history()` could have been moved directly into the new handlers.

Rejected because this would combine the introduction of CQRS with a larger behavioral refactor. The existing functions are already proven by earlier tests and can be reused safely.

### Introduce generic Command and Query base classes

Rejected because the concrete types require no shared behavior yet.

### Introduce CommandBus and QueryBus

Rejected because direct handler invocation is sufficient for the current number of operations. There is no routing problem to solve.

### Add parameters to OrderPlacementHistoryQuery

Rejected because no business requirement currently needs them.

### Wire Redis directly inside the Django View

Rejected because the HTTP adapter should not become the infrastructure composition root merely to make the CQRS path appear complete.

## Result

NovaTrade now has explicit CQRS concepts on both sides of the Application:

```text
✓ Command
✓ Command Handler
✓ Query
✓ Query Handler
```

The Command side expresses an intention to change business state and executes through transactional and event-publication dependencies.

The Query side expresses a request for information and executes through a dedicated historical read abstraction without loading `Order` aggregates.

The architecture does not include:

```text
✗ generic Command base class
✗ generic Query base class
✗ CommandBus
✗ QueryBus
✗ mediator framework
✗ separate read/write databases
✗ speculative read DTOs
✗ production CQRS composition wiring
```

Those remain future decisions that require their own pressure.

## TDD Evidence

Chapter 27 evolved through four explicit RED/GREEN steps.

### RED 1 — Place Order needs an explicit Command

The test required `PlaceOrderCommand`.

The failure was:

```text
ModuleNotFoundError:
No module named 'novatrade.application.commands'
```

GREEN introduced `PlaceOrderCommand` with `order_id` and `placed_at`.

### RED 2 — The Command needs a Handler

The test required `PlaceOrderCommandHandler`.

The failure was:

```text
ModuleNotFoundError:
No module named 'novatrade.application.commands.place_order_handler'
```

GREEN introduced the handler and delegated execution to `place_order_and_publish()`.

The command-side verification passed:

```text
12 passed in 0.11s
```

### RED 3 — Historical reads need an explicit Query

The test required `OrderPlacementHistoryQuery`.

The failure was:

```text
ModuleNotFoundError:
No module named 'novatrade.application.queries'
```

GREEN introduced the parameterless Query representing the current historical read request.

### RED 4 — The Query needs a Handler

The test required `OrderPlacementHistoryQueryHandler`.

The failure was:

```text
ModuleNotFoundError:
No module named 'novatrade.application.queries.order_placement_history_handler'
```

GREEN introduced the handler and delegated execution to the existing historical read use case.

The complete Chapter 27 unit slice passed:

```text
15 passed in 0.17s
```

The complete NovaTrade test suite then passed:

```text
95 passed in 2.02s
```

## Architectural Principle

> **Commands express intentions to change the system. Queries express requests to learn from it. Their models should be allowed to differ when their responsibilities differ.**

CQRS does not require symmetry, buses, separate databases, or a framework. It begins when the Application stops forcing fundamentally different operations through the same conceptual model.

A second principle emerged during the final inspection:

> **Introducing an Application interface does not automatically mean every external adapter is composed through it.**

Application architecture and runtime composition are related decisions, but they are not the same decision.

## Status

**Accepted.**

Chapter 26 established genuine pressure for CQRS by introducing a historical read path that did not require `Order` aggregates.

Chapter 27 makes that separation explicit through `PlaceOrderCommand`, `PlaceOrderCommandHandler`, `OrderPlacementHistoryQuery`, and `OrderPlacementHistoryQueryHandler`.

The implementation is verified by **95 passing tests**.

The Django HTTP placement edge still invokes the older use-case interface directly because production composition for `RedisEventPublisher` and the Command Handler has not yet been introduced. That limitation is explicit and remains a separate architectural pressure.
