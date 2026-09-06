# Empty Order Placement

## Context

NovaTrade clarified that the Customer places an Order.

## Business Rule

An empty Order cannot be placed.

## RED

We expressed the rule with the first domain test:

```python
def test_empty_order_cannot_be_placed():
    order = Order()

    with pytest.raises(CannotPlaceEmptyOrder):
        order.place()
```

The first execution failed because the Domain Model did not yet exist:

```text
ModuleNotFoundError: No module named 'domain'
```

## GREEN

We introduced the smallest implementation capable of satisfying the rule.

`Order.place()` raises `CannotPlaceEmptyOrder`.

At this point every Order is empty because the model has no way to add products yet.

The test passed.

## REFACTOR

We moved the production code into a conventional `src/` package layout:

```text
src/
└── novatrade/
    └── domain/
        └── order.py
```

NovaTrade is installed as an editable Python package through `pyproject.toml`.

The application is imported as:

```python
from novatrade.domain.order import Order
```

`src` is a packaging directory, not part of the application's package name and not an architectural layer.

After the refactor, the test remained green.

## What We Deliberately Did Not Add

We did not introduce:

- Order status
- Order ID
- Product
- Quantity
- Repository
- Unit of Work
- Django
- database persistence
- generic validation framework

None of these concepts is required to enforce the current business rule.

## Evidence

```text
tests/unit/domain/test_order.py
```

proves that an empty Order cannot be placed.

After the packaging refactor:

```text
1 passed
```

## Open Pressure

Every Order in the current model is empty.

NovaTrade now needs a way to add a Product to an Order before that Order can ever be successfully placed.

That pressure belongs to the next step in the model's evolution.
