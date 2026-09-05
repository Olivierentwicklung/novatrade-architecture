# 017 — Translate Errors at Boundaries

## Context

The HTTP API introduced in Chapter 18 could successfully place an existing
Order, but failures exposed a language problem across architectural boundaries.

When an Order did not exist, Django raised `OrderRecord.DoesNotExist`.
Without translation, that persistence-specific exception escaped through the
Application and reached the HTTP adapter as an internal server error.

A different failure appeared when an existing empty Order was placed.
In that case, the Domain raised `CannotPlaceEmptyOrder`, which already expressed
the failure in business language.

The two failures originated in different architectural layers and therefore
did not require identical treatment.

## Decision

Translate errors at the boundary where one architectural language meets another.

The Django repository translates:

`OrderRecord.DoesNotExist` → `OrderNotFound`

`OrderNotFound` belongs to the Application's repository vocabulary and does not
depend on Django.

The HTTP adapter translates:

`OrderNotFound` → `404 Not Found`

and:

`CannotPlaceEmptyOrder` → `409 Conflict`

The Domain and Application remain unaware of HTTP semantics.

We do not introduce an Application wrapper around
`CannotPlaceEmptyOrder` because the Domain exception already expresses the
business failure without infrastructure-specific vocabulary.

We also do not introduce a generic exception hierarchy, global HTTP exception
handler, or standardized error response format because the current requirements
do not create pressure for those abstractions.

## Consequences

Persistence-specific exceptions do not leak beyond the persistence adapter.

HTTP status codes remain an HTTP adapter concern.

Domain failures can remain in Domain language when that language is already
meaningful to callers.

Different failures may cross different numbers of translation boundaries.

The architecture does not require artificial symmetry between persistence,
Application, Domain, and HTTP errors.

Future error-handling abstractions should be introduced only when repeated
translation creates sufficient pressure.

## Principle

**Errors speak the language of the layer or technology that produces them.
Translate them when they cross a boundary.**

And:

**Do not wrap meaningful business language merely to make the architecture
look symmetrical.**
