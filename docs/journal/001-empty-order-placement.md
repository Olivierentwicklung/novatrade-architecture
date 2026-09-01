# Empty Order Placement

## Context

NovaTrade clarified that the customer places an Order.

## Business Rule

An empty Order cannot be placed.

## What We Tried

We expressed the rule directly through the Order:

```python
order.place()
```

## Decision

`Order` currently rejects placement unconditionally because all Orders are empty in the current model.

## Why

This is the smallest implementation satisfying the known rule.

## What We Deliberately Did Not Add

- Order status
- Order ID
- Repository
- database model
- Django
- generic validation framework

None is required yet.

## Test That Proves It

```text
tests/unit/domain/test_order.py
::test_empty_order_cannot_be_placed
```

## Open Pressure

NovaTrade needs a way to add products before an Order can ever be successfully placed.
