# 028 — We Said Django Was an Adapter. Prove It.

## Context

For many chapters, NovaTrade has been structured around a claim: Django is an adapter around the business application, not the owner of it.

By the end of Chapter 29, that claim was supported by dependency direction and by system-level tests. The Domain did not import Django. The Application expressed use cases through commands, handlers, ports, and business operations. Django handled HTTP and persistence concerns at the edges.

But good dependency diagrams are not enough.

If Django really is an inbound adapter, another HTTP framework should be able to invoke the same business operation without requiring the Domain or Application to be rewritten.

Chapter 30 therefore turns an architectural claim into an experiment:

> Can NovaTrade place an Order through Flask while keeping the existing Domain and Application unchanged?

The purpose is not to compare Django and Flask or decide which framework is better. Flask is introduced because a second HTTP framework gives us a concrete way to test whether the first one truly owns the business logic.

## Pressure

The existing Django place-order endpoint already performs a clear adapter responsibility. It receives an HTTP request, constructs a `PlaceOrderCommand`, delegates to `PlaceOrderCommandHandler`, and translates known NovaTrade failures into HTTP responses.

The question is whether those responsibilities can be implemented by another HTTP framework while everything behind the adapter boundary remains the same.

The desired flow is:

```text
Flask POST /orders/<order_id>/place
        ↓
PlaceOrderCommand
        ↓
PlaceOrderCommandHandler
        ↓
existing Application
        ↓
existing Domain
```

The architectural success criterion is deliberately strict:

```text
Domain changes       = 0
Application changes  = 0
```

If introducing Flask requires new business services, Flask-specific commands, duplicated validation, or changes to the Domain, then the earlier claim that Django is merely an adapter would need to be reconsidered.

## Decision

Introduce Flask as a second inbound HTTP adapter while reusing the existing `PlaceOrderCommand` and `PlaceOrderCommandHandler`.

Flask should remain idiomatic at its own edge. The adapter therefore uses a Flask application factory, Flask `Blueprint`, Flask route declarations, Flask error handlers, and Flask's `test_client()`.

The center of the system should not become Flask-aware.

The guiding rule is:

> Flask should look like Flask at the edge. NovaTrade should look like NovaTrade at the center.

The experiment changes one architectural variable at a time. Flask replaces Django as the inbound HTTP adapter for the place-order operation, but the existing Django ORM persistence adapter remains in use.

This is intentional.

Replacing an inbound adapter does not require replacing an unrelated outbound adapter.

## TDD Evidence

### RED 1 — The Flask adapter did not exist

The first adapter test described the required behavior before any Flask adapter code existed.

It attempted to import:

```python
from novatrade.adapters.flask.app import create_app
```

Pytest failed during collection with:

```text
ModuleNotFoundError:
No module named 'novatrade.adapters.flask'
```

This was a genuine RED. The Application capability already existed, but there was no Flask entry point into it.

The smallest implementation introduced the Flask adapter package and an application factory:

```text
src/novatrade/adapters/flask/
├── __init__.py
└── app.py
```

At this stage, `create_app()` created a Flask application but deliberately registered no order route.

### RED 2 — Flask existed, but did not speak the required HTTP vocabulary

Running the same test again moved the failure forward.

The Flask application could now be created and its `test_client()` could issue the request, but:

```text
POST /orders/<order_id>/place
```

returned:

```text
404 NOT FOUND
```

The adapter existed, but the required HTTP operation did not.

That pressure justified introducing the order Blueprint and route:

```text
src/novatrade/adapters/flask/order_api/
├── __init__.py
└── routes.py
```

The route constructs the existing `PlaceOrderCommand` and delegates it to the injected `PlaceOrderCommandHandler`.

No Flask-specific command or application service was introduced.

The test became GREEN.

### RED 3 — `OrderNotFound` escaped as HTTP 500

The next requirement concerned failure translation.

The existing Django adapter translated `OrderNotFound` into HTTP 404. Flask needed to preserve the same external semantics without moving HTTP knowledge into the Application.

A test handler deliberately raised the existing `OrderNotFound`.

The result was:

```text
Expected: 404
Actual:   500
```

The traceback showed the exception crossing the Flask boundary without translation.

The Flask adapter registered an error handler:

```text
OrderNotFound → HTTP 404
```

The Application exception remained unchanged.

The tests became GREEN.

### RED 4 — `CannotPlaceEmptyOrder` escaped as HTTP 500

The next test exposed a Domain failure through the same adapter.

`CannotPlaceEmptyOrder` expresses a business rule: an empty Order cannot be placed. The Domain owns that decision. It should not know that HTTP 409 exists.

Without adapter translation, Flask returned:

```text
Expected: 409
Actual:   500
```

The Flask adapter therefore added:

```text
CannotPlaceEmptyOrder → HTTP 409
```

Again, neither the Domain nor Application changed.

The focused Flask adapter suite reached:

```text
3 passed
```

At this point, further spy-based tests would mostly have tested additional Flask mechanics. The central architectural claim required stronger evidence.

## System Proof

The next test reused the system vocabulary already established in Chapter 29.

Chapter 29 had proven a flow in which a real Order was persisted through `DjangoOrderRepository`, the place-order operation was entered through Django/DRF, and the resulting `OrderPlaced` event crossed a real Redis boundary.

Chapter 30 changed the inbound HTTP adapter while deliberately keeping the rest of that architecture intact.

The new system flow became:

```text
Flask test_client()
        ↓
Flask Blueprint
        ↓
PlaceOrderCommand
        ↓
real PlaceOrderCommandHandler
        ↓
place_order_and_publish()
        ↓
DjangoUnitOfWork
        ↓
Domain
        ↓
RedisEventPublisher
        ↓
real Redis
        ↓
RedisEventReceiver
```

The test used the existing production `place_order_handler_factory(redis)` rather than assembling a Flask-specific business stack.

### Immediate GREEN

The system-level test passed on its first execution:

```text
1 passed
```

There was no RED.

This is significant and must not be rewritten as a conventional RED/GREEN sequence merely to make the development story look cleaner.

The test passed immediately because the architecture created in previous chapters already allowed another inbound adapter to drive the existing application.

> An immediate GREEN is evidence, not a failed TDD exercise.

No production implementation was added in response to this test because the test did not expose a missing production capability.

## An Important Boundary Discovery

Flask still used `DjangoUnitOfWork` behind the Application.

At first glance, that can sound contradictory: if Flask replaces Django, why is Django still present?

The answer is that two different adapter boundaries are involved.

```text
                 NovaTrade Core
                /              \
               /                \
      inbound adapters       outbound adapters
       /          \           /          \
    Django       Flask    Django ORM     Redis
     HTTP         HTTP
```

Django's HTTP adapter and Django ORM persistence adapter are separate architectural roles.

Chapter 30 replaces the former, not the latter.

Introducing Flask-SQLAlchemy, a Flask repository, or a second Unit of Work would have changed multiple variables simultaneously and weakened the experiment. There was no requirement demanding another persistence technology.

The experiment therefore produced a more precise lesson:

> Replacing an inbound adapter does not require replacing an unrelated outbound adapter.

## Tooling Issue — Not Architectural Pressure

The first full-suite run did not execute because pytest encountered two test modules with the same basename:

```text
tests/e2e/api/test_place_order_api.py
tests/unit/adapters/flask/test_place_order_api.py
```

Pytest reported an import-file mismatch.

This was not a TDD RED and revealed nothing about NovaTrade's production architecture. The Flask tests already passed independently, and the failure occurred during test collection because of Python module naming.

The Flask unit test was renamed to:

```text
tests/unit/adapters/flask/test_flask_place_order_adapter.py
```

No production code changed.

This distinction matters:

> A failing command is not automatically architectural pressure.

Tooling failures, test-discovery problems, and environment mistakes should not be rewritten as evidence that the business architecture required a new abstraction.

## Result

After resolving the test-module naming collision, the complete suite passed:

```text
103 passed in 2.28s
```

The final architectural result is:

```text
Django HTTP path          ✓
Flask HTTP path           ✓
Existing Application      unchanged
Existing Domain           unchanged
Existing persistence      reused
Existing Redis boundary   reused
Full regression suite     ✓
```

The original success criterion was therefore satisfied:

```text
Domain changes       = 0
Application changes  = 0
```

## What We Deliberately Did Not Add

Chapter 30 did not introduce:

- Flask-SQLAlchemy
- a Flask-specific repository
- a Flask-specific Unit of Work
- a Flask-specific command
- duplicated business validation
- a dependency-injection container
- Flask-RESTX
- Flask-Smorest
- Marshmallow
- a command bus
- another persistence technology

None of those abstractions or technologies were required to answer the architectural question.

Adding them would have made the experiment larger while making its conclusion less precise.

## Architectural Consequences

The architecture now has executable evidence that the place-order use case is not owned by Django's HTTP layer.

Both HTTP frameworks can perform their framework-specific responsibilities at the edge and converge on the same Application command:

```text
       Django                         Flask
          │                              │
       APIView                       Blueprint
          │                              │
          └──────────────┬───────────────┘
                         │
                         ▼
                PlaceOrderCommand
                         │
                         ▼
             PlaceOrderCommandHandler
                         │
                         ▼
                    Application
                         │
                         ▼
                       Domain
```

This does not mean NovaTrade is framework-free. A running application always depends on concrete technologies somewhere.

The architectural achievement is more specific: framework dependencies are located at boundaries where they can be replaced without forcing the business model to change.

That is what it means, in this system, to say:

> **Django is an adapter.**

And now the repository can prove it.

## Principles Reinforced

> **No architectural claim without proof.**

A dependency diagram can suggest framework independence. A second working adapter demonstrates it.

> **Framework independence does not mean framework avoidance.**

Django and Flask are both useful. The goal is not to hide them, but to keep their responsibilities at the appropriate boundary.

> **Adapters are independently replaceable dimensions.**

Replacing HTTP does not imply replacing persistence, messaging, or every technology associated with the original framework.

> **An immediate GREEN is evidence.**

When a new architectural test passes without production changes, that can demonstrate that earlier design decisions already created the capability being tested.

> **A failing command is not automatically architectural pressure.**

Tooling and test-organization failures must be distinguished from failures that reveal missing production behavior.

> **No pattern without pressure. No infrastructure without a requirement. No architectural claim without proof.**
