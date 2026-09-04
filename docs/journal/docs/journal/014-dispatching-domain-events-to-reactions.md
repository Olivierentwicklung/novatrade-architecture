# Architecture Journal 014 — Dispatching Domain Events to Reactions

## Context

An Order can now record the business fact that it was successfully placed as an `OrderPlaced` Domain Event. The Application can collect that event after executing the placement operation, allowing the fact to leave the aggregate without making the Domain responsible for what happens next.

Once that fact became available outside the aggregate, NovaTrade acquired independent business consequences for it. The customer must receive an order confirmation, while fulfillment must be notified so that processing can begin.

Neither consequence belongs inside `Order`. The aggregate owns the rules for placing an Order and knows when placement succeeds, but it should not know which parts of the system are interested in that fact.

## Pressure

A single reaction can be called directly without creating much architectural pressure. The situation changes when several independent behaviors care about the same event.

Without a separate coordination responsibility, some caller would need to know every consequence of `OrderPlaced`:

```text
OrderPlaced
    │
    ├── send customer confirmation
    └── notify fulfillment
```

As more reactions are added, that caller would accumulate knowledge about analytics, inventory, loyalty, or any other behavior interested in order placement.

The problem is therefore not that the reactions themselves are complicated. The problem is that knowledge of **who cares about an event** needs somewhere to live.

## Decision

Introduce an `EventDispatcher` in the Application layer.

The dispatcher owns the relationship between an event type and the reactions interested in that event. When an event is dispatched, every registered reaction for that event type receives it.

Conceptually:

```text
                         OrderPlaced
                              │
                              ▼
                       EventDispatcher
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
      send_order_confirmation()     notify_fulfillment()
```

The Domain remains responsible only for producing the business fact. Individual reactions remain responsible only for their own consequence. The dispatcher coordinates the relationship between them.

The first implementation is intentionally narrow. `OrderPlaced` is currently the only Domain Event type, so the dispatcher works directly with that concrete event rather than introducing a generic `DomainEvent` hierarchy.

## Reactions Are Not Primary Use Cases

`place_order()` represents an explicit application intention: someone asks NovaTrade to place an Order.

`send_order_confirmation()` and `notify_fulfillment()` are different. They happen because `OrderPlaced` already occurred. They are consequences of a business fact rather than primary intentions entering the system.

For that reason, these reactions are not placed under `application/use_cases/`. They remain Application behavior, but their role is different from the use case that caused the event.

This distinction also avoids making the Domain responsible for external consequences. `Order.place()` records `OrderPlaced`; it does not send confirmations, notify fulfillment, or know that those capabilities exist.

## External Capabilities Remain Ports

Both reactions require capabilities outside the Application.

Customer confirmation depends on `OrderConfirmationSender`, while fulfillment notification depends on `FulfillmentNotifier`. These are Application Ports because the Application needs the capabilities but should not depend on the technical mechanisms that eventually provide them.

```text
send_order_confirmation()
          │
          ▼
OrderConfirmationSender
          │
          ▼
    external adapter


notify_fulfillment()
          │
          ▼
 FulfillmentNotifier
          │
          ▼
    external adapter
```

No SMTP, queue, HTTP client, or other delivery technology is required by the Application-level decision.

## Alternatives Considered

### Put the reactions inside `Order`

Rejected because the aggregate should protect business rules and record what happened, not coordinate external consequences. Doing so would couple the Domain to concerns such as confirmation delivery and fulfillment integration.

### Call every reaction directly from `place_order()`

This would work for the current two reactions, but it would make the use case accumulate knowledge about every component interested in `OrderPlaced`. Each new reaction would require modifying the producer-side orchestration.

The use case should perform the business operation. It should not become the registry of everything that cares about the resulting business facts.

### Let the caller invoke every reaction

Returning Domain Events makes this technically possible:

```text
place_order()
     │
     ▼
(OrderPlaced,)
     │
     ▼
caller invokes every consequence
```

This merely moves the coupling outward. The caller would still need to know the complete set of reactions interested in each event.

### Introduce a Generic `DomainEvent` Base Class

Not introduced. NovaTrade currently has one concrete Domain Event, `OrderPlaced`. There is no demonstrated need for polymorphic Domain Event behavior or a shared event hierarchy.

The dispatcher can become more general when additional event types create that pressure.

### Introduce a Full Message Bus

Not introduced. The current problem is specifically dispatching a Domain Event to multiple interested reactions. A broader Message Bus abstraction could eventually coordinate commands, events, or other messages, but those requirements do not yet exist.

`EventDispatcher` names the responsibility NovaTrade actually has today.

## Consequences

The producer of `OrderPlaced` no longer needs to know every behavior interested in that fact.

Multiple reactions can evolve independently. Customer confirmation and fulfillment notification have separate dependencies and can be tested without involving the aggregate or each other.

The Application now contains an explicit coordination concept for Domain Events, while the Domain remains free of infrastructure and reaction-specific dependencies.

There is, however, an intentionally unresolved question:

```text
place_order()
     │
     ▼
OrderPlaced
     │
     ?
     ▼
EventDispatcher
```

NovaTrade has not yet decided when dispatch should occur relative to the Unit of Work. It has also not defined what should happen when one reaction succeeds and another fails.

Those are not merely dispatching questions. They concern transactions, consistency, and failure boundaries and therefore require separate architectural pressure.

## What We Are Not Introducing

At this stage NovaTrade does not introduce:

- a generic `DomainEvent` base class;
- a generic event-handler interface;
- a full Message Bus;
- asynchronous processing;
- a queue or worker;
- an event store;
- Event Sourcing;
- SMTP or other concrete confirmation infrastructure;
- fulfillment infrastructure;
- transaction-aware event dispatch;
- retry or failure-handling policies.

These concepts may become justified later, but none is necessary to solve the current problem.

## Principle

The Domain owns the fact that something happened. Reactions own what should happen because of that fact. The dispatcher owns the knowledge of who cares.

**The producer knows what happened. The dispatcher knows who cares. Each reaction knows what to do.**
