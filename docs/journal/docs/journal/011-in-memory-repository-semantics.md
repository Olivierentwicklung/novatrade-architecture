# Architecture Journal 011 — In-Memory Repository Semantics

## Context

NovaTrade now has two adapters implementing the `OrderRepository` Port:

- `InMemoryOrderRepository`
- `DjangoOrderRepository`

Both provide the same Application-facing operations:

```python
def get(self, order_id: UUID) -> Order:
    ...

def remember(self, order: Order) -> None:
    ...
```

Structurally, both adapters satisfied the Port. Their behavior, however, was not equivalent.

The Django adapter persists an Order as database state. A later `get()` reconstructs a new Domain object from that persisted state.

The in-memory adapter originally stored the `Order` object itself:

```python
def remember(self, order: Order) -> None:
    self._orders[order.id] = order

def get(self, order_id: UUID) -> Order:
    return self._orders[order_id]
```

This meant that the caller, repository, and subsequent calls to `get()` could all hold references to the same mutable `Order` instance.

As a result, changing an Order after `remember()` could silently change what the repository appeared to contain without another call to `remember()`.

The in-memory adapter therefore satisfied the repository Port structurally while violating an important persistence behavior.

## Pressure

The expected behavior is:

> Changes to an Order are not preserved until the repository is explicitly asked to remember them.

A failing test exposed that the in-memory repository did not provide this behavior.

An Order was remembered and then modified without calling `remember()` again. When the Order was retrieved from the repository, the modification was already visible.

The repository had not preserved state at the moment `remember()` was called. It had preserved a reference to a mutable Python object.

Correcting that behavior exposed a second issue in existing Application tests. Those tests asserted that the original `Order` object supplied before calling `place_order()` had changed.

They passed previously only because the in-memory repository returned the same object instance.

Once the repository stopped sharing mutable aggregate references, those tests failed even though the use case correctly loaded, placed, and remembered the Order.

The tests were therefore observing Python object identity rather than the persisted result of the Application operation.

## Decision

The in-memory repository will preserve independent `Order` instances across its persistence boundary.

When `remember(order)` is called, the repository creates an independent representation of the current Order state.

When `get(order_id)` is called, the repository returns another independent Order instance rather than exposing its internally stored instance.

The adapter reuses the Domain's existing reconstitution capability:

```python
Order.reconstitute(
    order_id=order.id,
    status=order.status,
    placed_at=order.placed_at,
    lines=order.lines,
)
```

This gives the in-memory adapter the persistence semantics currently required by the Application without introducing another persistence model.

Application tests must observe persisted results through the repository rather than relying on mutation of previously held object references.

For example, after:

```python
place_order(...)
```

the test retrieves the Order again:

```python
placed_order = orders.get(order.id)
```

and asserts against `placed_order`.

## Why Reconstitution

Chapter 12 already established a distinction between creating a new Order, performing business behavior, and restoring historical state:

```text
Order()                    → create a new Order
order.place(placed_at)     → perform business
Order.reconstitute(...)    → restore an existing Order
```

The in-memory repository now needs to create an Order representing state that has already been remembered.

Reconstitution already expresses that concept.

Using it avoids replaying business operations merely to reconstruct repository state.

## Alternatives Considered

### Store the Original Order Reference

Rejected.

This was the previous implementation. It allows mutations outside the repository to change remembered state without an explicit `remember()` operation.

It also allows objects returned by `get()` to mutate repository state directly.

That makes the in-memory adapter behavior materially different from the Django persistence adapter.

### `copy.deepcopy()`

Considered but not chosen.

`deepcopy()` could break shared references, but it expresses a Python object-copying mechanism rather than the Domain concept involved.

The repository needs to preserve and restore an Order, not generically clone an arbitrary Python object graph.

It would also couple repository behavior to the copyability of the aggregate's internal object structure.

### Introduce a Separate In-Memory Snapshot Model

Considered but not required by the current pressure.

The repository could translate an Order into primitive stored values and reconstruct the Domain object from that snapshot. This would resemble database persistence more closely.

However, introducing another persistence representation would add concepts that the current problem does not require.

Reconstitution provides the behavioral semantics needed now with less machinery.

## Consequences

The in-memory repository no longer exposes shared mutable `Order` instances across the persistence boundary.

After:

```python
repository.remember(order)
```

later mutations of `order` do not change remembered state unless `remember(order)` is called again.

Likewise, after:

```python
retrieved = repository.get(order_id)
```

mutating `retrieved` does not change repository state unless it is explicitly remembered.

This makes the in-memory and Django adapters more behaviorally consistent even though their underlying technologies remain completely different.

The change also makes Application tests stronger. They now verify the preserved result of a use case rather than relying on implementation-specific object identity.

## What We Are Not Introducing

This decision does not introduce:

- a generic repository base class,
- a repository mapper abstraction,
- a dedicated snapshot type,
- serialization infrastructure,
- `deepcopy()`-based persistence,
- repository contract tests,
- a Unit of Work.

Those concepts require their own pressure before being added.

## Principle

Implementing the same Port is not enough.

Two adapters can satisfy the same method signatures while providing materially different behavior.

An in-memory adapter does not need to imitate the technology of a database, but it should preserve the behavioral semantics on which the Application relies.

**Interface compatibility is not the same as behavioral equivalence.**
