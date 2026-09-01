# Architecture Journal 003 — OrderLine Becomes a Value Object

## Context

NovaTrade's Ordering Domain already supported adding Products with a Quantity to an Order.

After Chapter 4, the Order represented its contents as:

```python
list[tuple[str, Quantity]]
```

For example:

```python
[
    ("BOOK-123", Quantity(2)),
]
```

This representation was sufficient for the business requirements we had at the time.

Each tuple contained the necessary data, and `Quantity` already protected the rule that a Product Quantity must be a positive integer.

There was not yet enough pressure to introduce another domain concept.

## New Pressure

Customer Service introduced a new requirement:

> We need to show the lines belonging to an Order.

The term **Order Line** was also becoming part of NovaTrade's business language.

A Product ID and its Quantity were no longer merely two values that happened to travel together. The business was referring to them together as one concept:

```text
Order Line
├── Product ID
└── Quantity
```

## Previous Representation

The Order stored:

```python
list[tuple[str, Quantity]]
```

This representation encoded meaning through position:

```python
("BOOK-123", Quantity(2))
```

The first position represented the Product ID.

The second represented the Quantity.

The data was correct, but the business concept remained implicit.

## First Decision

Introduce `OrderLine`:

```python
@dataclass(frozen=True)
class OrderLine:
    product_id: str
    quantity: Quantity
```

The Order could then represent its contents as:

```python
list[OrderLine]
```

Instead of tuple unpacking, the model could now speak explicitly in domain language:

```python
line.product_id
line.quantity
```

## Evidence from the Refactoring

Changing the representation exposed code that still depended on the tuple structure.

The existing tests revealed those dependencies incrementally.

The first failure showed that an older test still expected:

```python
("BOOK-123", Quantity(2))
```

instead of an `OrderLine`.

The next failure occurred because `change_quantity()` attempted to unpack an `OrderLine` as a tuple.

After that was corrected, `quantity_for()` exposed the same assumption.

The migration therefore showed that introducing a domain concept was more than renaming data. Code that previously depended on positional structure had to begin working through the concept itself.

After the representation change, the complete test suite was green.

## Additional Business Pressure

NovaTrade then introduced another rule:

> Adding the same Product again increases its Quantity.

For example:

```text
Add BOOK-123 × 2
Add BOOK-123 × 3
```

must result in:

```text
BOOK-123 × 5
```

not:

```text
BOOK-123 × 2
BOOK-123 × 3
```

The first implementation of `OrderLine` did not satisfy this rule.

The failing test demonstrated that the Order created two separate lines for the same Product.

## Decision

An Order contains at most one `OrderLine` for a Product.

When the same Product is added again, the Order combines the existing and added Quantities and replaces the previous immutable `OrderLine` with a new one.

Conceptually:

```text
OrderLine(BOOK-123, Quantity(2))
                +
          Quantity(3)
                ↓
OrderLine(BOOK-123, Quantity(5))
```

The `Order` currently controls this operation because the rule concerns the consistency of the Order's collection of lines.

## Why OrderLine Is a Value Object

`OrderLine` has business meaning, but it currently has no independent business identity.

Consider:

```python
OrderLine(
    product_id="BOOK-123",
    quantity=Quantity(2),
)
```

and another `OrderLine` containing the same Product ID and Quantity.

NovaTrade currently considers them equivalent.

Their meaning is determined by their values rather than by an independent identity.

Therefore `OrderLine` is currently modeled as a Value Object.

## Value Semantics

Executable tests verify that two `OrderLine` instances containing the same values compare as equal.

They also verify that an `OrderLine` is immutable.

The current implementation uses:

```python
@dataclass(frozen=True)
```

This is a convenient Python implementation technique.

It is not what makes `OrderLine` a Value Object.

The domain semantics come first:

- equality is determined by values;
- the concept has no independent business identity;
- replacement is preferable to mutation.

## Persistence Does Not Define Domain Identity

A future persistence implementation may store Order Lines in a database table.

That table may have a technical primary key such as:

```text
id = 42
```

That does not automatically make `OrderLine` a Domain Entity.

Database identity and business identity solve different problems.

`OrderLine` should become an Entity only if NovaTrade eventually needs to distinguish and track a particular Order Line independently through time.

No such requirement exists yet.

## What We Learned

The transition was:

```text
Product ID + Quantity
        ↓
repeatedly travel together
        ↓
business names the combination
        ↓
OrderLine becomes explicit
        ↓
new behavior concerns lines
        ↓
the concept gains architectural significance
```

A class was not introduced merely because two values could be grouped together.

The abstraction became useful because the business language and behavior increasingly treated those values as one concept.

## Trade-offs

The Order currently searches its list of Order Lines when it needs to locate a Product.

A dictionary could provide faster lookup.

At the current scale and with the current requirements, the simpler representation is sufficient.

We will not optimize the structure without evidence that lookup performance has become a meaningful problem.

## Deliberately Not Added

We did not introduce:

- `OrderLineId`
- an `OrderLine` repository
- a Product Entity
- a `ProductId` Value Object
- a generic Value Object base class
- Quantity arithmetic operators
- an `increase_by()` method merely to move behavior
- a generic validation framework
- additional architectural layers

None currently solves enough business or technical pressure to justify its cost.

## Evidence

The Chapter 5 implementation was developed through failing and passing tests.

The repository demonstrated:

```text
OrderLine missing
        ↓
OrderLine introduced
        ↓
old tuple assumptions exposed
        ↓
representation migrated
        ↓
tests green
        ↓
duplicate Product behavior requested
        ↓
failing test
        ↓
Quantities combined
        ↓
tests green
        ↓
Value Object semantics verified
```

At the final Chapter 5 implementation checkpoint, the complete suite reported:

```text
16 passed in 0.09s
```

## Open Pressure

The Order now contains meaningful `OrderLine` and `Quantity` Value Objects.

But the model still allows its contents to be modified after the Order has been placed.

Conceptually, nothing yet prevents:

```text
Customer places Order
        ↓
Customer adds another Product
```

or:

```text
Customer places Order
        ↓
Customer changes Quantity
```

NovaTrade says that once an Order is placed, its submitted contents must stop changing.

That rule applies across multiple operations and multiple objects inside the Order.

The next architectural question is therefore:

> **Who is responsible for protecting the consistency of the Order and everything inside it?**

That pressure will drive the next architectural discovery.
