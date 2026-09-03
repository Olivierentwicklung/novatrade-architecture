# Architecture Journal — Chapter 14: What Is One Business Operation?

## Context

At the beginning of Chapter 14, the Application layer could load an `Order`, execute the domain operation, and preserve the changed aggregate through an `OrderRepository`.

The `place_order()` use case was conceptually:

```python
order = orders.get(order_id)
order.place(placed_at)
orders.remember(order)
```

This was sufficient to preserve one changed `Order`, but it did not express the boundary of the complete application operation.

The architectural question for this chapter became:

> What constitutes one business operation, and which layer should define its persistence boundary?

---

## Decision 1 — `Repository.remember()` Does Not Mean “Operation Complete”

### Pressure

`OrderRepository.remember()` has a narrow responsibility: preserve an `Order`.

That is different from saying that every persistence change belonging to the `Place Order` application operation has completed successfully.

Treating repository persistence as equivalent to application-operation completion would couple the meaning of the operation to one particular aggregate save.

### Initial Decision

Introduce an application-level `Committer` port:

```python
class Committer(Protocol):
    def commit(self) -> None:
        ...
```

The use case could then distinguish between preserving an aggregate and completing the persistence operation:

```python
order = orders.get(order_id)
order.place(placed_at)
orders.remember(order)
committer.commit()
```

### Result

The new behavior passed its test, but the design exposed another problem.

The `OrderRepository` and `Committer` were independent dependencies.

Nothing guaranteed that they participated in the same persistence boundary.

### Status

**Superseded.**

The `Committer` was useful as an intermediate abstraction because it exposed the distinction between saving an aggregate and completing an application operation.

It did not survive the final design.

---

## Decision 2 — Persistence Resources for One Operation Belong Together

### Pressure

The Application could receive:

```python
place_order(
    orders=some_repository,
    committer=some_committer,
    ...
)
```

The type system expressed no relationship between those collaborators.

The repository could theoretically operate against one persistence context while the committer controlled another.

The stronger requirement became:

> The persistence resources participating in one application operation must belong to one persistence boundary.

### Decision

Replace the independent `OrderRepository` and `Committer` dependencies with a `UnitOfWork`.

The Unit of Work exposes the repositories participating in the operation:

```python
class UnitOfWork(Protocol):
    @property
    def orders(self) -> OrderRepository:
        ...
```

The use case therefore obtains its repository from the same persistence boundary:

```python
order = work.orders.get(order_id)
```

### Consequence

The Application no longer assembles unrelated persistence collaborators.

The Unit of Work becomes the Application-facing abstraction representing the persistence resources belonging to one operation.

---

## Decision 3 — Expose the Repository as Read-Only Through the Port

### Pressure

The first `UnitOfWork` protocol represented the repository as a mutable protocol attribute:

```python
orders: OrderRepository
```

A test double using:

```python
self.orders = InMemoryOrderRepository()
```

produced a structural typing incompatibility because mutable protocol attributes are invariant.

More importantly, the Application does not need permission to replace the repository participating in the Unit of Work.

It only needs access to it.

### Decision

Expose `orders` as a read-only property:

```python
@property
def orders(self) -> OrderRepository:
    ...
```

### Consequence

The port now expresses the actual requirement more precisely:

> The Application may use the Order repository belonging to this Unit of Work.

It does not imply:

> The Application may replace that repository.

The typing problem therefore revealed a useful design distinction rather than something to suppress.

---

## Decision 4 — The Application Owns the Unit of Work Scope

### Pressure

Introducing a `UnitOfWork` object did not yet define when the operation began or ended.

The use case could use:

```python
work.orders
```

and call persistence operations without explicitly entering a transactional boundary.

A Unit of Work object is not automatically a Unit of Work scope.

### Evidence

A new test required the use case to execute inside the boundary.

The actual RED was:

```text
7 collected
6 passed
1 failed

assert work.entered
E assert False
```

### Decision

Make the Unit of Work a context manager and let the Application use case own its scope:

```python
with work:
    order = work.orders.get(order_id)
    order.place(placed_at)
    work.orders.remember(order)
```

### Rationale

The Application layer knows what `Place Order` means.

Django does not.

Therefore the Application should decide which work belongs to the operation, while infrastructure should implement the technical mechanism required to enforce that boundary.

### Consequence

Responsibility is divided as follows:

```text
Application
    |
    | defines what belongs to one operation
    v
UnitOfWork Port
    ^
    | implements the boundary
    |
Infrastructure
```

---

## Decision 5 — Remove Explicit `commit()` From the Final Unit of Work Contract

### Pressure

After introducing context-manager semantics, the Django implementation naturally mapped the Unit of Work to:

```python
transaction.atomic()
```

Django commits an atomic block when it exits successfully and rolls it back when an exception leaves the block.

An explicit Application call:

```python
work.commit()
```

therefore resulted in a Django implementation whose `commit()` method did nothing:

```python
def commit(self) -> None:
    pass
```

The interface no longer described the real behavior.

### Decision

Remove explicit `commit()` from the final `UnitOfWork` port.

Remove the corresponding call from `place_order()`.

Successful completion of the Unit of Work scope now represents successful persistence:

```python
with work:
    ...
```

Normal exit preserves the work.

Exceptional exit rolls it back.

### Consequence

Earlier tests asserting:

```python
assert work.committed
```

became obsolete and were removed.

Their historical value remains preserved in Git.

The final test suite tests observable transaction semantics instead of an implementation-level boolean.

---

## Decision 6 — Django Implements the Boundary With `transaction.atomic()`

### Pressure

The Unit of Work abstraction would be incomplete if it worked only with test doubles.

Chapter 13 already demonstrated that behavioral assumptions based only on in-memory implementations can be misleading.

The Django adapter therefore needed to prove real atomic behavior.

### Decision

Implement:

```text
DjangoUnitOfWork
        |
        v
transaction.atomic()
```

The adapter enters a Django atomic transaction when the Unit of Work scope begins and leaves it when the scope ends.

### Failure Semantics

An integration test modifies persisted state inside the Unit of Work and then raises an exception.

After leaving the boundary, the changed state is reloaded.

The changes made during the failed operation do not survive.

Therefore:

```text
exception
    ↓
leave UnitOfWork
    ↓
Django transaction rollback
```

### Success Semantics

A complementary integration test modifies persisted state and leaves the Unit of Work normally.

The changes survive.

Therefore:

```text
successful completion
    ↓
leave UnitOfWork
    ↓
Django transaction commit
```

The success test passed immediately because `transaction.atomic()` already provided the required behavior.

No artificial RED was created.

---

## Rejected / Superseded Alternatives

### Repository Persistence as the Operation Boundary

Rejected because `remember(order)` describes preservation of one aggregate, not completion of an entire application operation.

### Separate Repository and Committer

Introduced temporarily and later superseded.

It made operation completion explicit but could not guarantee that repository operations and commit belonged to the same persistence boundary.

### Explicit `UnitOfWork.commit()`

Introduced during discovery and later removed.

Once scope-based semantics were mapped to Django's `transaction.atomic()`, an explicit `commit()` became ceremonial rather than behavioral.

Keeping it would make the abstraction less truthful.

### Let Django Define the Transaction Boundary

Rejected.

Django knows how to execute a transaction but does not know what constitutes the `Place Order` application operation.

Allowing infrastructure to determine the business-operation boundary would reverse the intended dependency direction.

---

## Final Architecture

```text
                 place_order()
                       |
                       | defines
                       v
              one application operation
                       |
                       v
                with UnitOfWork
                       |
               +-------+-------+
               |               |
          load Order      preserve Order
               |               |
               v               |
        domain behavior        |
               |               |
               +-------+-------+
                       |
                       v
                  leave scope
                  /         \
             success       exception
                |              |
                v              v
             persist        rollback
```

Dependency direction:

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

The Application defines **what belongs to one operation**.

The Unit of Work port expresses that requirement without depending on Django.

The Django adapter defines **how that operation becomes atomic**.

---

## Architectural Principle

A transaction and a business operation are related, but they are not the same concept.

A transaction is a technical persistence mechanism.

A business operation belongs to the Application language.

`transaction.atomic()` cannot know where `Place Order` begins and ends.

`place_order()` can.

Therefore:

> **The Application defines the boundary. Infrastructure enforces it.**

---

## TDD / Discovery Notes

Chapter 14 did not begin by deciding to implement the Unit of Work pattern.

The architecture emerged through successive pressure:

```text
OrderRepository
       |
       v
Saving an Order does not express operation completion
       |
       v
Repository + Committer
       |
       v
Those collaborators may belong to different boundaries
       |
       v
UnitOfWork
       |
       v
Having a UnitOfWork object does not define its lifetime
       |
       v
Application-owned UnitOfWork scope
       |
       v
Explicit commit becomes redundant with real Django semantics
       |
       v
Scope-based UnitOfWork
       |
       v
Django transaction.atomic()
       |
       +--> success   -> persist
       |
       +--> exception -> rollback
```

The `Committer` therefore should not be considered a failed design.

It was a useful intermediate model that exposed the next architectural question.

Likewise, not every test needed to fail first. The successful Django transaction test passed immediately because the already-selected infrastructure mechanism provided that behavior.

The governing principle remains:

> **No pattern without pressure.**

That does not mean manufacturing pain or artificial RED tests. It means that every architectural decision should have an observable reason for existing.

---

## Verification

At the Chapter 14 implementation checkpoint:

- Unit of Work scope is owned by the Application.
- Failed Django Unit of Work changes are rolled back.
- Successful Django Unit of Work changes are preserved.
- Previous Domain and persistence behavior remains intact.
- Full test suite: **50 passed**.

The working tree was clean after the Chapter 14 implementation commit.

---

## Chapter 14 Outcome

Chapter 14 began with a repository and a seemingly complete `place_order()` use case.

It ends with a clear distinction between:

- changing an aggregate,
- preserving an aggregate,
- defining an application operation,
- and enforcing that operation atomically.

The Unit of Work earned its place because the Application needed a name and a boundary for persistence work that belongs together.

The resulting rule is simple:

> **The Application decides what one operation is. The adapter makes that operation atomic.**
