# 006 — Order Identity and Entity Semantics

## Context

Until Chapter 8, an `Order` was defined entirely by its behavior and state. It contained `OrderLine` objects, protected its business rules, and controlled its lifecycle through `OrderStatus`. This was sufficient while every Order existed only as a single object during a test or operation.

A new business requirement introduced a different problem: NovaTrade needs to distinguish one Order from another. Two customers may create Orders containing exactly the same Products and Quantities, but those Orders are still different business objects.

This means the contents of an Order are not sufficient to determine which Order it is.

## Decision

Every `Order` has a unique identity represented by a UUID.

When a new Order is created without an existing identity, the Domain generates one:

```python
self.id = order_id if order_id is not None else uuid4()
```

The constructor can also receive an existing identity:

```python
Order(order_id=existing_id)
```

This allows an Order that already exists to be reconstructed without accidentally becoming a new Order.

Order equality is based on identity:

```python
def __eq__(self, other: object) -> bool:
    if not isinstance(other, Order):
        return NotImplemented

    return self.id == other.id
```

Two `Order` instances with the same identity therefore represent the same business Order, even though they are different Python objects.

Conversely, two Orders with identical contents but different identities remain different Orders.

## Architectural Meaning

The introduction of identity changes how `Order` is understood in the Domain Model.

`Quantity` and `OrderLine` have value semantics. Two instances containing the same values can be considered equal because their values define what they are.

`Order` has entity semantics. Its Products, Quantities, and lifecycle status may change over time without turning it into another Order. What preserves continuity is its identity.

Therefore, `Order` is now explicitly understood as an **Entity** and continues to act as the Aggregate Root of the ordering Aggregate.

This distinction emerged from business requirements rather than from introducing a Domain-Driven Design abstraction in advance.

## Alternatives Considered

### Use Order contents as identity

Rejected.

Two independent Orders may contain exactly the same Products and Quantities. Their contents therefore cannot reliably distinguish them.

### Use an incrementing integer

Not chosen at this stage.

Generating sequential identifiers normally introduces responsibility for coordinating identity generation with persistence or another external mechanism. Persistence has not yet entered the architecture.

A UUID allows the Domain to create an identity without depending on a database or framework.

### Introduce an `OrderId` Value Object

Deferred.

A UUID currently satisfies the requirements for Order identity. There are no additional business rules, validation requirements, parsing rules, or behaviors associated with an Order ID that justify another Domain abstraction.

An `OrderId` Value Object may be introduced later if new requirements create sufficient pressure.

### Introduce an `Entity` base class

Deferred.

`Order` is currently the only Domain object requiring Entity semantics. Introducing inheritance would create an abstraction before duplication or another concrete requirement demonstrates its value.

Being an Entity is currently a modeling concept, not a requirement for a Python superclass.

### Implement `__hash__`

Deferred.

There is no requirement to use `Order` instances as dictionary keys or members of sets. Because `Order` is mutable and equality is identity-based, leaving it unhashable is an appropriate default until a concrete use case requires otherwise.

## Consequences

An Order now has continuity independent of its current state and contents.

New Orders receive unique identities without depending on persistence infrastructure. Existing Orders can retain their identities when reconstructed. Equality between Orders expresses business identity rather than Python object identity or structural equality.

The Domain Model now contains both Value Objects and an Entity, allowing their different equality semantics to be demonstrated through executable tests.

The decision also introduces an important constraint for future persistence work: storing and reconstructing an Order must preserve its identity. A persistence mechanism that generates a new Domain identity every time an Order is loaded would represent the business incorrectly.

No persistence implementation is introduced by this decision.

## Evidence

The decision is protected by tests demonstrating that:

- a new Order receives an identity;
- different Orders receive different identities even when their contents are identical;
- an Order can be created with an existing identity;
- two Order instances with the same identity compare as equal;
- Orders with identical contents but different identities compare as different.

At the Chapter 8 implementation checkpoint, the complete test suite contains **36 passing tests**.

## Principle Reinforced

**No pattern without pressure.**

Identity was introduced because the business needed to distinguish Orders. Entity semantics followed because multiple objects can represent the same business Order.

`OrderId`, an `Entity` superclass, hashing behavior, repositories, database identifiers, and persistence mechanisms were deliberately not introduced because the Domain does not yet require them.
