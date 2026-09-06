# Architecture Journal 026 — The Application Needs to Be Assembled

## Context

Chapter 27 introduced an explicit Command and Query boundary into NovaTrade's Application layer.

Placing an Order could now be expressed as an intention:

```text
PlaceOrderCommand
        │
        ▼
PlaceOrderCommandHandler
        │
        ▼
place_order_and_publish()
```

The handler itself did not know how persistence or event transport worked. Instead, it depended on abstractions already earned by earlier architectural pressure:

```text
PlaceOrderCommandHandler
        │
        ├── UnitOfWork
        └── EventPublisher
```

Concrete implementations already existed:

```text
UnitOfWork
    └── DjangoUnitOfWork

EventPublisher
    └── RedisEventPublisher
```

The individual pieces worked.

But the running application had a problem that Chapter 27 intentionally left unresolved:

> Who constructs the concrete objects and connects them to the Application handler?

A `PlaceOrderCommandHandler` could not execute by itself. Something eventually had to know that NovaTrade's production implementation used a `DjangoUnitOfWork` and a `RedisEventPublisher`.

The abstractions had separated responsibilities successfully. They had not eliminated the need for concrete construction.

---

## Pressure

Inspection of the production code revealed that concrete dependencies were being constructed in several places.

The Django HTTP adapter directly created objects such as:

```text
DjangoUnitOfWork()
DjangoOrderRepository()
```

At the same time, there was no production construction of:

```text
PlaceOrderCommandHandler(...)
RedisEventPublisher(...)
```

This meant the Command architecture introduced in Chapter 27 existed at the Application level, but the real Django application still bypassed it.

The first requirement became:

> The application must provide an assembled `PlaceOrderCommandHandler` whose concrete infrastructure dependencies are created outside the Django HTTP adapter.

The initial instinct was to create a factory under the Application package.

A failing test looked for:

```text
novatrade.application.place_order_handler_factory
```

and failed because the module did not exist.

That RED was useful, but examining the proposed dependency direction revealed a deeper problem. If the factory lived inside `application/`, it would have to import concrete implementations such as:

```text
DjangoUnitOfWork
RedisEventPublisher
```

The Application layer would then know about the infrastructure adapters that were supposed to depend on it.

The proposed location was wrong.

The failing test had exposed not merely a missing module, but a misplaced responsibility.

---

## Decision 1 — Introduce an Explicit Composition Root

Object assembly belongs outside the Application layer.

NovaTrade therefore introduced a small bootstrap boundary:

```text
src/novatrade/bootstrap/
```

The composition test moved accordingly:

```text
tests/unit/bootstrap/
```

The bootstrap factory assembled the concrete production graph:

```text
DjangoUnitOfWork
        │
        ├──────────────┐
        │              │
        ▼              ▼
UnitOfWork      RedisEventPublisher
                       │
                       ▼
                 EventPublisher
        │              │
        └──────┬───────┘
               ▼
    PlaceOrderCommandHandler
```

The resulting factory remained deliberately small.

It did not introduce:

- a dependency injection container,
- a service locator,
- a generic factory framework,
- a CommandBus,
- automatic dependency discovery,
- or a global application container.

There was no pressure for those mechanisms.

The Composition Root existed for one concrete reason: some part of the system had to know which implementations should satisfy the Application handler's dependencies.

---

## Decision 2 — Keep Infrastructure Configuration Injectable

The first bootstrap implementation received a Redis client:

```text
place_order_handler_factory(redis=...)
```

This preserved a useful boundary.

The factory knew how to combine:

```text
DjangoUnitOfWork
RedisEventPublisher
PlaceOrderCommandHandler
```

but the Redis connection itself could still be supplied from outside.

This allowed the composition test to use `FakeRedis` without changing Application behavior.

When runtime composition later required a production Redis client, the factory was extended so that production could request:

```text
place_order_handler_factory()
```

while tests could continue to provide:

```text
place_order_handler_factory(redis=FakeRedis())
```

The resulting seam was not introduced because dependency injection was fashionable. It survived because two real environments required different infrastructure construction.

---

## Pressure — The HTTP Adapter Still Bypassed the Command

Assembling the handler did not mean the running application used it.

`PlaceOrderView` still executed the older Application path directly:

```text
HTTP
  │
  ▼
PlaceOrderView
  │
  ▼
place_order()
```

The newly introduced Command Handler was therefore disconnected from the real HTTP entry point.

The next requirement became:

> When an HTTP request asks to place an Order, `PlaceOrderView` must create a `PlaceOrderCommand` and execute it through its handler.

An initial test attempted to prove that the view could receive a handler:

```text
PlaceOrderView(handler=handler)
```

Unexpectedly, the test passed immediately.

That result was important precisely because it was not a RED.

The test had only demonstrated behavior already provided by the framework. It had not demonstrated that NovaTrade's HTTP adapter delegated the request through the Command architecture.

The test was therefore not treated as architectural evidence.

A better test used a spy handler and required the HTTP request to produce and delegate a `PlaceOrderCommand`.

That test failed because the existing view continued into `DjangoUnitOfWork` and attempted database access.

This was the genuine RED.

It demonstrated that the HTTP adapter was still executing the old path.

---

## Decision 3 — Make the Handler an Explicit HTTP Adapter Dependency

`PlaceOrderView` was changed so that it no longer constructed a `DjangoUnitOfWork` or directly called the old `place_order()` use case.

Instead, it translated HTTP input into an Application command:

```text
HTTP request
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

The view retained responsibility for translating Application and Domain failures into HTTP responses.

It did not take responsibility for constructing the handler.

This preserved the adapter's role:

```text
HTTP language
     ↓
Application language
```

rather than:

```text
HTTP
 ↓
framework adapter
 ↓
construct infrastructure
 ↓
execute business operation
```

The focused unit test passed.

But that success revealed the next pressure.

---

## Pressure — Unit Composition Was Not Runtime Composition

The unit test explicitly constructed the view with a handler.

The real Django application did not.

The existing end-to-end tests failed with:

```text
AttributeError:
'PlaceOrderView' object has no attribute 'handler'
```

This failure was particularly valuable because no new test had to be invented.

The existing HTTP tests already described the required behavior:

- an Order can be placed,
- an unknown Order returns `404`,
- an empty Order returns `409`.

Changing the view had broken those established guarantees.

The problem was no longer whether the handler could be assembled or whether the view could use it.

Both were already proven.

The missing connection was:

```text
Composition Root
       │
       X
       │
       ▼
Django runtime
       │
       ▼
PlaceOrderView
```

Creating a Composition Root was not sufficient.

The running application had to enter through it.

---

## Decision 4 — Wire the Composition Root at Django's Outer Edge

Inspection showed that Django constructed the HTTP adapter through:

```text
PlaceOrderView.as_view()
```

in the URL configuration.

The URL configuration was therefore the point where the framework could receive the already assembled Application behavior.

NovaTrade connected the pieces there:

```text
Django URL configuration
        │
        ▼
place_order_handler_factory()
        │
        ├── DjangoUnitOfWork
        └── RedisEventPublisher
        │
        ▼
PlaceOrderCommandHandler
        │
        ▼
PlaceOrderView
```

The URL configuration does not need to know how the handler performs the business operation.

The view does not need to know how its dependencies are constructed.

The Application handler does not need to know which HTTP framework invoked it.

The concrete pieces meet at the outer boundary.

---

## Framework Discovery — A Type Annotation Is Not Runtime Configuration

The first runtime wiring attempt used:

```text
PlaceOrderView.as_view(handler=...)
```

while `PlaceOrderView` declared the dependency only through a type annotation.

The focused unit tests still passed.

The end-to-end tests did not.

Django rejected the URL configuration because `as_view()` accepts initialization keyword arguments only when the corresponding name already exists as a runtime class attribute.

A declaration such as:

```text
handler: PlaceOrderCommandHandler
```

helps static analysis, but it does not create a runtime class attribute.

The dependency therefore became explicitly configurable at runtime:

```text
handler: PlaceOrderCommandHandler | None = None
```

and the view guards against execution without a configured handler.

This was not a reason to redesign the architecture.

It was a framework-specific constraint discovered at the adapter boundary.

The architecture accommodated the framework without allowing the framework to determine the Application design.

---

## Result

The real runtime path now becomes:

```text
HTTP POST
    │
    ▼
Django URL configuration
    │
    ▼
Composition Root
    │
    ├── DjangoUnitOfWork
    │
    └── RedisEventPublisher
    │
    ▼
PlaceOrderCommandHandler
    │
    ▼
PlaceOrderView
    │
    ▼
PlaceOrderCommand
    │
    ▼
Application operation
    │
    ├── Domain
    ├── persistence
    └── event publication
```

The Django HTTP adapter no longer constructs the Unit of Work for the place-Order operation.

The Application layer does not import Django or Redis infrastructure in order to assemble itself.

The Composition Root is the deliberate place where concrete infrastructure and Application behavior meet.

---

## A Failure That Was Not Architectural Pressure

After the runtime wiring passed its focused and end-to-end tests, the complete test suite initially failed during collection.

The problem was a duplicate Python test-module basename:

```text
tests/unit/application/use_cases/test_place_order.py

tests/unit/bootstrap/test_place_order.py
```

Pytest imported one `test_place_order` module and then encountered another module with the same import name.

The bootstrap test was renamed to:

```text
test_place_order_composition.py
```

No production architecture changed.

This failure was deliberately not classified as another TDD RED.

It was a tooling/test-discovery problem.

That distinction matters.

Not every red terminal output represents architectural pressure.

A useful architectural RED demonstrates that required system behavior cannot currently be satisfied.

A collection error caused by duplicate module names demonstrates that the test runner cannot discover the tests correctly.

Conflating the two would distort both the development history and the architectural reasoning.

---

## Verification

After the composition test received a unique module name, the complete NovaTrade suite passed:

```text
97 passed in 3.32s
```

This verifies the new composition path without sacrificing the behavior established by previous chapters.

---

## Rejected Alternatives

### Put the factory inside the Application layer

Rejected because the factory would need to import concrete Django and Redis adapters.

That would reverse the intended dependency direction.

### Construct everything inside `PlaceOrderView`

Rejected because the HTTP adapter would become responsible for infrastructure construction as well as HTTP translation.

The view should consume Application behavior, not assemble the system.

### Construct Redis directly inside the URL configuration

Rejected because URL routing should not accumulate infrastructure configuration and object-graph construction.

The URL configuration is an appropriate place to connect Django to an already defined composition boundary, not to become the composition mechanism itself.

### Introduce a dependency injection container

Rejected because the object graph is currently small and explicit.

A container would solve complexity NovaTrade does not yet have.

### Introduce a CommandBus

Rejected because Chapter 28's problem is object composition, not command routing.

`PlaceOrderCommandHandler` can be invoked directly.

### Generalize all factories

Rejected because only one concrete composition problem currently demands this structure.

Generalization would predict future pressure rather than respond to existing pressure.

### Refactor every Django read view immediately

Rejected because `OrderDetailView` and `OrderListView` were not the source of the Chapter 28 pressure.

Their current construction choices may create future pressure, but this chapter does not assume that they will.

---

## Architectural Consequences

NovaTrade now has an explicit Composition Root.

The Application layer continues to depend on abstractions rather than concrete infrastructure implementations.

Infrastructure adapters remain replaceable at the boundary where the application is assembled.

The Django HTTP adapter receives Application behavior rather than constructing the business execution graph itself.

Tests can substitute infrastructure such as `FakeRedis` at the composition boundary without modifying Application code.

The cost is that the outermost application wiring now explicitly knows about concrete implementations. This is intentional.

Somewhere must know.

The goal of dependency inversion is not to make concrete dependencies disappear. It is to control where knowledge of them is allowed to exist.

---

## Principle Earned

> **Dependency inversion determines which way dependencies point. Composition determines where the concrete pieces finally meet.**

A second lesson also became clearer:

> **A Composition Root is useful only when the running application actually enters through it.**

And the chapter reinforced the project's existing rule:

> **No pattern without pressure.**

NovaTrade did not introduce a dependency injection framework because clean architecture diagrams often contain one.

It introduced the smallest possible composition boundary because the running application had concrete objects that needed to be assembled without pulling infrastructure knowledge into the Application layer.

The pattern followed the pressure.
