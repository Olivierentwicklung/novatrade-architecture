# Architecture Journal 012 — Unit of Work Transaction Boundary

## Context

NovaTrade's `place_order()` Application use case can load an existing `Order`, perform the Domain operation, and preserve the changed aggregate through the `OrderRepository` Port:

```python
order = orders.get(order_id)
order.place(placed_at)
orders.remember(order)
```

The repository gives the Application a persistence abstraction for Orders, but `remember(order)` describes preservation of one aggregate.

It does not define when the complete Application operation begins or ends.

This distinction became important once the Application needed to express that the persistence work belonging to `Place Order` forms one operation.

The architectural question became:

> Which abstraction represents the persistence boundary of one Application operation, and which layer decides where that boundary begins and ends?

## Pressure

The first pressure was the distinction between preserving an `Order` and completing an Application operation.

An intermediate `Committer` Port made that distinction explicit:

```python
order = orders.get(order_id)
order.place(placed_at)
orders.remember(order)
committer.commit()
```

This solved the immediate problem but exposed another one.

The `OrderRepository` and `Committer` were independent dependencies. Nothing guaranteed that they participated in the same persistence boundary.

The Application could theoretically receive:

```python
place_order(
    order_id=order.id,
    orders=some_repository,
    placed_at=placed_at,
    committer=some_committer,
)
```

where `some_repository` and `some_committer` represented unrelated persistence contexts.

The stronger requirement therefore became:

> Persistence resources participating in one Application operation must belong to one persistence boundary.

Introducing a single persistence object exposed another distinction.

Having an object representing a Unit of Work is not the same as executing inside a Unit of Work boundary.

A failing test demonstrated that `place_order()` could use the persistence object without defining when the operation began or ended.

The Application therefore needed both a persistence boundary and explicit ownership of its lifetime.

## Decision

Introduce a `UnitOfWork` Port representing the persistence resources belonging to one Application operation.

The Unit of Work exposes the `OrderRepository` participating in that operation:

```python
class UnitOfWork(Protocol):
    @property
    def orders(self) -> OrderRepository:
        ...
```

The repository is exposed as a read-only property because the Application needs to use the repository belonging to the Unit of Work, not replace it.

The Unit of Work also defines a context-manager boundary:

```python
def __enter__(self) -> "UnitOfWork":
    ...

def __exit__(
    self,
    exc_type,
    exc_value,
    traceback,
) -> bool | None:
    ...
```

The Application use case owns that scope:

```python
with work:
    order = work.orders.get(order_id)
    order.place(placed_at)
    work.orders.remember(order)
```

This assigns two different responsibilities:

```text
Application          → defines what belongs to one operation
Persistence adapter  → enforces that boundary technically
```

The Django adapter implements the Unit of Work using `transaction.atomic()`.

A normal exit from the Unit of Work preserves the changes performed during the operation.

An exception leaving the Unit of Work causes Django to roll back those changes.

## Why the Application Owns the Boundary

Django knows how to execute a database transaction.

It does not know what constitutes the `Place Order` Application operation.

If infrastructure determined the transaction scope, the technical persistence mechanism would decide where an Application operation begins and ends.

Instead, `place_order()` defines the scope:

```python
with work:
    ...
```

and the adapter translates that scope into the persistence mechanism appropriate for its technology.

For Django:

```text
Application UnitOfWork scope
            ↓
DjangoUnitOfWork
            ↓
transaction.atomic()
```

This preserves the dependency direction established by the architecture.

The Application defines the requirement.

The adapter implements it.

## Alternatives Considered

### Treat `remember()` as the Operation Boundary

Rejected.

`remember(order)` means that an `Order` should be preserved.

It does not express completion of all persistence work belonging to an Application operation.

Equating aggregate persistence with operation completion would make the boundary depend on one repository call.

### Separate `OrderRepository` and `Committer`

Introduced temporarily but superseded.

A separate `Committer` made operation completion explicit, but nothing guaranteed that it controlled the same persistence context as the repository.

The intermediate abstraction was useful because it exposed the need for a stronger boundary.

### Explicit `UnitOfWork.commit()`

Introduced during discovery but not retained in the final contract.

Once the Unit of Work became a context manager and the Django implementation used `transaction.atomic()`, successful transaction completion occurred when the scope exited normally.

The Django adapter therefore temporarily required a `commit()` method that performed no work:

```python
def commit(self) -> None:
    pass
```

Keeping that method would make the Application-facing abstraction imply behavior that the adapter did not actually perform.

The final Unit of Work therefore uses scope completion rather than an explicit `commit()` call.

### Let Django Define the Transaction Scope

Rejected.

Django can provide transaction mechanics, but it does not own the meaning of the Application use case.

The persistence technology should enforce the boundary rather than determine it.

## Consequences

`place_order()` now executes all persistence work inside one explicit Unit of Work scope.

The repository used by the operation belongs to that Unit of Work rather than being supplied independently.

The Application remains independent of Django:

```text
Application
    |
    v
UnitOfWork Port
    ^
    |
DjangoUnitOfWork
    |
    v
transaction.atomic()
```

The Django adapter provides real transaction semantics.

If work inside the Unit of Work fails with an exception, changes performed during that operation do not survive.

If the Unit of Work completes successfully, the changes are preserved.

The success behavior required no additional implementation after `transaction.atomic()` was introduced because Django already provided the required semantics.

The final tests therefore verify observable persistence behavior rather than an internal `committed` flag.

## What We Are Not Introducing

This decision does not introduce:

- Domain Events,
- an Event Bus,
- asynchronous processing,
- multiple aggregates participating in `Place Order`,
- payment transactions,
- inventory reservations,
- a generic transaction manager,
- a generic repository registry,
- a production in-memory Unit of Work,
- framework transaction logic inside the Application layer.

Those concepts require their own pressure before being added.

## Principle

A business operation and a database transaction are related, but they are not the same abstraction.

The Application knows what work belongs to `Place Order`.

The persistence adapter knows how to make that work atomic using its underlying technology.

**The Application defines the boundary. Infrastructure enforces it.**
