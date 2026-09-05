# Architecture Journal 016 — HTTP as an Adapter

## Context

Until now, NovaTrade could perform the Order placement business operation without exposing it through HTTP.

The Domain knew how an Order could be placed. The Application layer coordinated that operation through `place_order()`. The Django persistence adapter implemented the repository and Unit of Work required to preserve both the changed Order and the `OrderPlaced` business fact.

What did not exist was an external HTTP entry point.

A new requirement introduced that pressure:

> A client needs to place an existing Order through HTTP.

This did not require a new business operation. It required a new way of reaching an existing one.

## Pressure

The arrival of HTTP exposed a structural weakness in the Django adapter.

When persistence was the only Django concern, a Django application named `persistence` appeared reasonable. It contained the Django models, repositories, migrations, and Unit of Work.

Once an API was introduced, continuing to organize primarily by technical role would have pushed the same Order capability into separate top-level technical areas.

Instead, the Django adapter was reorganized around the business capability first:

```text
order_app/
├── api/
├── persistence/
├── migrations/
├── apps.py
└── models.py
```

Within the Order capability, technical responsibilities remain separated. `api` handles the HTTP-facing side, while `persistence` handles the database-facing side.

The Domain itself did not move into `order_app`. The business model remains in `novatrade.domain`, and the use case remains in `novatrade.application`.

`order_app` is still part of the Django adapter.

## Decision

Expose Order placement as an explicit business action:

```text
POST /api/orders/{order_id}/place/
```

The API is implemented as a thin adapter.

Its responsibility is to translate an HTTP request into a call to the existing Application use case:

```text
HTTP
  │
  ▼
PlaceOrderView
  │
  ▼
place_order(...)
  │
  ▼
Domain + Unit of Work
```

The view does not load the Order directly, execute `Order.place()`, persist models directly, create `OrderPlacedRecord` itself, or manage the database transaction.

Those responsibilities already have homes elsewhere in the architecture.

## Evidence

The first end-to-end API test initially could not even be collected because Django REST Framework was not installed.

That failure provided concrete pressure for introducing DRF rather than adding the framework in anticipation of future needs.

After DRF became available, the same test exposed another missing piece: Django could not reverse the `order-place` route.

That pressure earned the API package and URL boundary:

```text
order_app/
└── api/
    ├── __init__.py
    ├── urls.py
    └── views.py
```

The first implementation returned HTTP 200 without performing the business operation. The HTTP test became green, but the result exposed an important limitation: a successful response did not prove that an Order had actually been placed.

The end-to-end scenario was therefore strengthened to create and persist an Order before sending the request and then reload it afterward.

The test failed because the persisted Order remained `DRAFT`.

That failure provided the pressure to connect `PlaceOrderView` to the existing `place_order()` Application use case through `DjangoUnitOfWork`.

Once that connection existed, the Order became `PLACED`.

The test was then strengthened again to verify that the `OrderPlaced` business fact was also persisted. This additional assertion passed immediately.

No new production code was required.

That immediate success demonstrated that the transactional behavior developed in the previous chapters remained intact when the operation was reached through HTTP.

The complete path is now:

```text
POST /api/orders/{order_id}/place/
              │
              ▼
       PlaceOrderView
              │
              ▼
        place_order()
              │
              ▼
      DjangoUnitOfWork
              │
       ┌──────┴──────┐
       ▼             ▼
 Order → PLACED   OrderPlaced
                  persisted
```

The full test suite passes with 66 tests.

## Consequences

HTTP is now another adapter around the existing Application rather than a new home for business logic.

The API can remain thin because Order placement already has a defined Application boundary.

The Django adapter is organized first around the Order capability and then around technical responsibilities within that capability.

The endpoint expresses the business action directly rather than exposing persistence vocabulary:

```text
POST /api/orders/{order_id}/place/
```

instead of treating placement as a generic update operation.

The end-to-end test verifies the complete vertical path from HTTP to durable business outcome.

## What We Deliberately Did Not Solve

The API currently handles only the successful Order placement path.

We did not yet translate missing Orders, invalid business transitions, or other Application and Domain failures into appropriate HTTP responses.

Those failures speak a different language from HTTP.

That is the next architectural pressure, not part of this decision.

We also did not introduce serializers, permissions, authentication, generic API abstractions, or additional endpoint infrastructure without a requirement that needs them.

## Principle

> **A thin adapter becomes possible when the business operation already has a proper home.**

HTTP does not own Order placement.

It provides another way to reach it.
