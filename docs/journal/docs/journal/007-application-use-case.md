# 007 — The First Application Use Case

## Context

Until Chapter 9, NovaTrade's architecture consisted almost entirely of the Domain Model. `Order` knew how to manage Products and Quantities, protect modification rules, move through its lifecycle, and preserve its identity.

This worked while tests and callers interacted directly with Domain objects.

A new requirement introduced a different question:

> How does the system execute a business use case?

NovaTrade needs customers to be able to place Orders. The Domain already knows what placing an Order means through:

```python id="3dw4wr"
order.place()
```

However, the act of executing a system-level use case is not itself another business rule of `Order`.

This created the first pressure for a layer outside the Domain Model.

## Decision

Introduce an `application` package containing the first Application use case:

```text id="h8qfsl"
src/
└── novatrade/
    ├── application/
    │   ├── __init__.py
    │   └── place_order.py
    └── domain/
```

The use case remains deliberately small:

```python id="51tfwd"
from novatrade.domain.order import Order


def place_order(order: Order) -> None:
    """Execute the use case of placing an Order."""
    order.place()
```

The Application layer coordinates the operation by asking the Domain to perform the business behavior.

It does not implement the placement rules itself.

## Why the Business Rule Remains in the Domain

An empty Order cannot be placed.

That rule already belongs to `Order`:

```python id="5x8p2s"
def place(self) -> None:
    if not self._lines:
        raise CannotPlaceEmptyOrder

    self.status = OrderStatus.PLACED
```

The Application use case therefore does not duplicate the rule:

```python id="6c2bhn"
def place_order(order: Order) -> None:
    if not order.lines:
        raise CannotPlaceEmptyOrder

    order.place()
```

Doing so would spread business knowledge across layers. A future caller that bypassed the Application function could then potentially encounter different behavior from one that used it.

Instead:

```text id="s30rhn"
Application
    │
    │ coordinates
    ▼
place_order(order)
    │
    │ delegates
    ▼
Domain
    │
    │ decides
    ▼
Order.place()
```

The Application layer determines that the use case should be executed.

The Domain determines whether the requested business operation is valid and performs the state transition.

## Architectural Meaning

Chapter 9 introduces a distinction between **business behavior** and **application orchestration**.

The Domain Model answers questions such as:

- Can this Order be placed?
- What makes an Order invalid for placement?
- What lifecycle transition occurs when placement succeeds?

The Application layer answers a different question:

- Which Domain operation should be executed for this use case?

This is the first boundary outside the Domain Model that has been earned by an actual requirement.

The Application layer depends on the Domain. The Domain does not depend on the Application layer.

```text id="ljkefc"
Application
     │
     ▼
   Domain
```

This dependency direction allows business behavior to remain independent of the way the system is invoked.

## Why the Use Case Is a Function

The first implementation is a function:

```python id="4ufgwj"
def place_order(order: Order) -> None:
    order.place()
```

No `PlaceOrderService` class has been introduced.

At this stage, a class would not provide additional behavior, state, dependencies, or coordination. Wrapping a single Domain call inside an object merely to use the word “service” would add structure without solving another problem.

If future requirements introduce dependencies or more complex orchestration, the shape of the use case can evolve under that pressure.

## Why There Is No Command or Handler

The architecture also does not introduce constructs such as:

```text id="dzk2ve"
PlaceOrderCommand
PlaceOrderHandler
CommandBus
```

The current use case has no requirement for message dispatch, command routing, middleware, or asynchronous execution.

Those abstractions may become useful later, but introducing them now would make the architecture describe anticipated complexity rather than existing complexity.

## The Deliberate Limitation

The current use case accepts an `Order`:

```python id="zkpcq9"
place_order(order)
```

This means the caller must already possess a Domain object.

That is not how the business naturally describes the operation. A caller is more likely to say:

```text id="r4uf25"
Place Order ABC.
```

The caller knows the identity of the Order, not necessarily the in-memory Python object representing it.

A more realistic interaction would eventually resemble:

```text id="ncl2h5"
Order ID
   │
   ▼
Application
   │
   ├── obtain Order
   │
   ▼
Order.place()
   │
   └── preserve resulting state
```

The current architecture cannot perform the missing steps.

That limitation is intentional.

Solving it would require answering questions about where Orders live, how they are retrieved, and how changes are preserved. Those problems have not yet been introduced by the current requirement.

The Application layer therefore remains incomplete rather than predicting the architecture needed to solve future requirements.

## Alternatives Considered

### Call `order.place()` directly everywhere

Possible, but rejected as the system-level design.

Direct Domain calls are appropriate inside tests and Domain-focused code, but the application needs a place where use cases can be expressed independently of delivery mechanisms.

Introducing the Application boundary gives the system a location for orchestration without moving business rules out of the Domain.

### Put placement validation in the Application layer

Rejected.

The rule that an empty Order cannot be placed is a business invariant of `Order`. Moving or duplicating it in Application code would weaken the Domain Model and distribute business knowledge across layers.

### Introduce a `PlaceOrderService` class

Deferred.

The current use case has no state or dependencies that require an object. A function communicates the behavior with less structure.

### Introduce a Repository

Deferred.

The current use case receives an existing `Order` object. No requirement has yet forced the Application layer to retrieve or preserve Orders.

Introducing a Repository now would solve a problem that this chapter has deliberately not reached.

### Introduce Commands and Handlers

Deferred.

There is currently no need for command dispatch, handler registration, middleware, or other command-processing infrastructure.

The simple function is sufficient.

## Consequences

NovaTrade now contains its first explicit Application layer.

The dependency direction remains clear:

```text id="lv8cj4"
Application
     │
     ▼
   Domain
```

Business rules remain protected by Domain objects, while Application code provides an entry point for executing a use case.

The implementation is intentionally thin. This is not considered a weakness that must immediately be corrected. Its simplicity accurately reflects the requirements that currently exist.

At the same time, the implementation exposes an important limitation: the Application use case requires the caller to provide an already available `Order`.

That limitation is preserved rather than hidden behind speculative infrastructure.

## Evidence

The decision is protected by tests demonstrating that:

- the Application use case can place a valid Order;
- attempting to place an empty Order through the Application use case still produces the Domain's `CannotPlaceEmptyOrder` rule.

The second test required no additional production implementation because the Application layer already delegated the decision to the Domain.

At the Chapter 9 implementation checkpoint, the complete NovaTrade test suite contains **38 passing tests**.

## Principle Reinforced

**No pattern without pressure.**

The Application layer was not created because the architecture was expected to contain one. It appeared when the system needed to express its first use case outside the Domain Model.

The implementation was not expanded into Services, Commands, Handlers, Repositories, or persistence abstractions because those concepts have not yet been required.

The architecture grows only as the problems grow.
