## Chapter 21 — Then NovaTrade Wants 100 Orders

### Pressure

NovaTrade's staff no longer wanted to retrieve only one Order by identity.

They needed:

> "Show me the latest 100 Orders."

The existing read path could retrieve a single Order and could initially be extended to return a collection, but the phrase "latest 100" introduced two new requirements:

- the result must be limited;
- the Orders must be ordered from newest to oldest.

This immediately raised a more fundamental question: what makes one Order newer than another?

### Decision

"Latest" means most recently created Order.

We did not use `placed_at`, because an Order can exist before it is placed and "latest Orders" does not mean "most recently placed Orders."

We also rejected UUID ordering and implicit database ordering because neither expresses the business meaning of "latest."

Creation time therefore became explicit Order state:

`Order.created_at`

The value remains explicit at the Domain boundary rather than being generated internally with `datetime.now()`.

The repository abstraction was then extended with:

`latest(limit: int) -> tuple[Order, ...]`

The Application expresses its requirement as:

`orders.latest(limit=100)`

while each adapter decides how to satisfy that requirement.

The Django adapter uses database ordering and limiting:

`ORDER BY created_at DESC`
`LIMIT 100`

### Why We Did Not Introduce CQRS

The read requirement became more specific, but the existing repository abstraction could still express it without distortion.

A separate query service, DTO, read model, or CQRS architecture would therefore solve a problem we had not yet demonstrated.

The collection read still returns Domain `Order` objects.

This is deliberate.

### Consequences

The Domain now represents when an Order was created.

Every repository adapter that reconstitutes Orders must preserve that state. This affected both the Django and in-memory adapters.

The Application no longer asks for every Order and discards unwanted results itself. It asks the repository for the latest 100, allowing the persistence adapter to perform ordering and limiting close to the data.

The implementation is behaviorally correct, but Django still reconstructs complete Domain Orders, including their lines.

For multiple Orders, this may have performance consequences.

We have not optimized that behavior because no performance requirement or measurement has yet justified a change.

### Principle

> A larger read does not automatically require a separate read architecture.

And:

> Let the Application express what it needs. Let the adapter decide how to retrieve it.

### Result

The complete test suite passes:

`80 passed in 1.07s`

The system can now serve:

`GET /api/orders/`

as the latest 100 Orders, newest first.

The solution is correct.

Whether it is efficient is a different question.
