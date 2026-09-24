# NovaTrade Architecture

> **An executable companion to _Building Software Around the Business — Not Around the Framework_.**

NovaTrade is a small Python backend application built to demonstrate how software architecture can **emerge from concrete business and technical pressure instead of being designed from a pattern checklist upfront**.

This repository is not a Clean Architecture starter template. It is the executable history behind the book. The implementation begins with business rules and gradually introduces Value Objects, application use cases, repository ports, Django persistence, a Unit of Work, Domain Events, HTTP adapters, read models, Redis messaging, commands and queries, composition, system-level architectural tests, and finally a second HTTP framework.

Every major architectural concept had to earn its place.

The project is guided by three principles:

> **No pattern without pressure.**
> **No infrastructure without a requirement.**
> **No architectural claim without proof.**

---

## Why This Repository Exists

Architecture is often presented from the end.

We see diagrams containing layers, ports, adapters, repositories, commands, queries, event buses, and infrastructure. What those diagrams usually cannot show is **why each boundary exists, what the system looked like before it was introduced, and which problem made the additional complexity worthwhile**.

NovaTrade approaches the problem from the opposite direction.

The project starts small. As new business and technical requirements appear, the existing design is allowed to become insufficient. Tests expose that pressure, the smallest responsible architectural change is introduced, and the system evolves from there.

The development rhythm is:

```text
Business conversation
        ↓
Precise requirement
        ↓
🔴 Failing test
        ↓
Simplest responsible implementation
        ↓
🟢 Passing test
        ↓
New pressure
        ↓
Architectural concept earns its place
        ↓
🔵 Refactor
```

Not every architectural test has to begin RED. Later in the project, some newly articulated architectural properties already pass because previous decisions created the required boundaries. Those immediate GREENs are preserved honestly as architectural evidence rather than rewritten into artificial failures.

---

## The Final Architecture

By the final executable checkpoint, NovaTrade has evolved into this structure:

```text
                         Inbound Adapters
                  ┌────────────┴────────────┐
                  │                         │
             Django / DRF                Flask
                  │                         │
                  └────────────┬────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     Application     │
                    │                     │
                    │ Commands · Queries  │
                    │ Handlers · Use Cases│
                    │ Ports · Reactions   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       Domain        │
                    │                     │
                    │ Orders · Quantity   │
                    │ Rules · State       │
                    │ Domain Events       │
                    └─────────────────────┘

                         Outbound Adapters
                  ┌────────────┴────────────┐
                  │                         │
             Django ORM                  Redis
             Persistence                Messaging
```

The important point is not the diagram itself.

**This was not the starting architecture.**

It is the accumulated result of the pressures encountered during the implementation.

---

## Architecture by Responsibility

### Domain

The Domain contains the business concepts and rules that should not depend on Django, Flask, Redis, HTTP, or database APIs.

```text
src/novatrade/domain/
├── events.py
├── order.py
└── quantity.py
```

This is where concepts such as Orders, quantities, state transitions, identity, invariants, and Domain Events live.

### Application

The Application coordinates business operations and defines the boundaries required from the outside world.

```text
src/novatrade/application/
├── commands/
├── ports/
├── queries/
├── reactions/
├── use_cases/
├── event_dispatcher.py
├── event_dispatcher_factory.py
├── list_order_placement_history.py
├── place_order_and_publish.py
└── process_next_event.py
```

The Application knows what the system needs to accomplish without owning the infrastructure used to accomplish it.

### Adapters

Concrete technologies live at the edges.

```text
src/novatrade/adapters/
├── django/
├── flask/
├── in_memory/
└── redis/
```

Django serves two independent roles in the final system:

- an **inbound HTTP adapter** through Django REST Framework;
- an **outbound persistence adapter** through Django ORM.

Flask provides a second inbound HTTP adapter.

Redis provides the process-boundary messaging adapter.

The in-memory adapters remain useful for focused tests and for demonstrating boundaries without requiring production infrastructure.

### Bootstrap / Composition

```text
src/novatrade/bootstrap/
├── place_order.py
└── process_events.py
```

Ports determine which direction dependencies point, but something still has to choose and construct the concrete implementations used by the running application.

NovaTrade keeps that responsibility explicit rather than introducing a dependency-injection container without a demonstrated need.

---

## Django Is an Adapter — and the Repository Proves It

One of the architectural claims developed throughout the project is that Django should remain at the edge rather than owning the business logic.

A package diagram alone does not prove that.

At the final implementation stage, NovaTrade introduces Flask as a second inbound HTTP adapter:

```text
Django HTTP
     │
     ▼
PlaceOrderCommand
     │
     ▼
PlaceOrderCommandHandler
     │
     ▼
Application → Domain
```

and:

```text
Flask HTTP
     │
     ▼
PlaceOrderCommand
     │
     ▼
PlaceOrderCommandHandler
     │
     ▼
Application → Domain
```

The experiment changed the inbound framework while requiring:

```text
Domain changes       = 0
Application changes  = 0
```

The Flask system test then drives the existing Application and Domain while continuing to use Django-backed persistence and Redis messaging.

Replacing one adapter does not require replacing an unrelated adapter.

That is the difference between drawing a framework boundary and demonstrating one.

---

## Commands and Queries

NovaTrade does not begin by declaring that it uses CQRS.

The distinction appears only after read and write requirements become meaningfully different.

The final Application contains explicit command and query models:

```text
application/
├── commands/
│   ├── place_order.py
│   └── place_order_handler.py
│
└── queries/
    ├── order_placement_history.py
    └── order_placement_history_handler.py
```

A command represents an intention to change the system.

A query represents a request for information.

The terminology is introduced after the separation has become useful rather than before the project has evidence that it needs it.

---

## Domain Events and Process Boundaries

When placing an Order becomes significant to other parts of the system, NovaTrade introduces the `OrderPlaced` Domain Event.

That does **not** immediately introduce Redis.

The architecture separates several responsibilities that are often collapsed under the label “event-driven architecture”:

```text
Business fact
    │
    ▼
OrderPlaced
    │
    ├── preserve ──────► EventRepository
    │
    ├── hand off ──────► EventPublisher
    │
    ├── transport ─────► Redis
    │
    ├── receive ───────► EventReceiver
    │
    └── interpret ─────► Application Dispatcher / Reactions
```

Redis arrives only when information actually has to cross from one running process to another.

> **The transport carries the fact. The Application decides what the fact means.**

---

## Test Strategy

The test suite is deliberately divided by the kind of evidence each test provides:

```text
tests/
├── unit/
├── integration/
└── e2e/
    ├── api/
    └── system/
```

### Unit Tests

Unit tests exercise Domain behavior, Application behavior, commands, queries, reactions, bootstrap decisions, and individual adapters with focused dependencies.

Examples include:

```text
tests/unit/domain/
tests/unit/application/
tests/unit/adapters/
tests/unit/bootstrap/
```

These tests answer questions such as:

- Does an Order protect its business rules?
- Does a command handler delegate correctly?
- Does an event reaction call the appropriate port?
- Does an HTTP adapter translate requests and errors correctly?

### Integration Tests

Integration tests exercise boundaries against real infrastructure behavior.

```text
tests/integration/adapters/django/
tests/integration/adapters/redis/
```

These tests verify concerns such as Django-backed persistence and communication across a real Redis process boundary.

### End-to-End Tests

The E2E tests exercise complete application paths.

```text
tests/e2e/api/
tests/e2e/system/
```

API tests drive the system through HTTP.

System tests go further and verify architectural flows across multiple real boundaries.

The later chapters deliberately ask architectural questions such as:

> If the individual pieces work, does the assembled system work?

and:

> If Django is really an inbound adapter, can another HTTP framework drive the same business operation without changing the core?

Tests are therefore not only used to verify features. They also provide evidence for important architectural claims.

---

## Technology Stack

The final executable implementation uses:

- Python 3.11+
- Django
- Django REST Framework
- Flask
- Redis
- pytest
- pytest-django
- Docker Compose
- SQLite for the Django persistence example

The purpose of the project is not to advocate for this exact stack. Each technology appears because a particular implementation pressure required a concrete adapter or testing environment.

---

## Requirements

You need:

- Python 3.11 or newer
- Git
- Docker with Docker Compose support

Create and activate a virtual environment.

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the project dependencies:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

---

## Start Redis

Redis is the external process-boundary infrastructure used by the final implementation.

Start it with Docker Compose:

```bash
docker compose up -d
```

The repository uses the `redis:8-alpine` image and exposes Redis on:

```text
localhost:6379
```

To stop the service:

```bash
docker compose down
```

---

## Django Database

Django's `manage.py` lives inside the Django adapter:

```text
src/novatrade/adapters/django/manage.py
```

Apply the migrations with:

```bash
python src/novatrade/adapters/django/manage.py migrate
```

The example uses SQLite, so no external relational database server is required.

---

## Run the Test Suite

From the repository root:

```bash
python -m pytest
```

At the final `chapter-30` checkpoint, the complete suite contains **103 passing tests**.

You can also run individual test layers:

```bash
python -m pytest tests/unit
```

```bash
python -m pytest tests/integration
```

```bash
python -m pytest tests/e2e
```

Or inspect one of the final architectural proofs directly:

```bash
python -m pytest tests/e2e/system/test_order_placement_flow.py
```

```bash
python -m pytest tests/e2e/system/test_order_processing_flow.py
```

```bash
python -m pytest tests/e2e/system/test_flask_order_placement_flow.py
```

---

## Project Structure

A simplified view of the final repository:

```text
novatrade-architecture/
│
├── src/
│   └── novatrade/
│       ├── domain/
│       │   ├── events.py
│       │   ├── order.py
│       │   └── quantity.py
│       │
│       ├── application/
│       │   ├── commands/
│       │   ├── ports/
│       │   ├── queries/
│       │   ├── reactions/
│       │   ├── use_cases/
│       │   ├── event_dispatcher.py
│       │   ├── place_order_and_publish.py
│       │   └── process_next_event.py
│       │
│       ├── adapters/
│       │   ├── django/
│       │   │   ├── core/
│       │   │   └── order_app/
│       │   ├── flask/
│       │   ├── in_memory/
│       │   └── redis/
│       │
│       └── bootstrap/
│           ├── place_order.py
│           └── process_events.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   │   ├── api/
│   │   └── system/
│   └── support/
│
├── docs/
│   └── architecture-journal/
│       ├── 001-empty-order-placement.md
│       ├── ...
│       └── 028-we-said-django-was-an-adapter-prove-it.md
│
├── compose.yaml
├── pyproject.toml
├── requirements.txt
└── README.md
```

The structure shown here is the **result** of the project, not the structure with which it began.

---

## Follow the Architecture Through Git

One of the most important features of this repository is its history.

The final source tree shows **what** NovaTrade became.

The Git history shows **why**.

Implementation chapters have annotated Git tags representing executable checkpoints:

```bash
git tag
```

To inspect a chapter exactly as it existed at that point:

```bash
git checkout chapter-14
```

For example, this allows you to study the system before and after important architectural decisions rather than seeing only the finished result.

To return to the current implementation:

```bash
git switch main
```

The final executable checkpoint is:

```text
chapter-30
```

Chapters 31 and 32 are retrospective book chapters and deliberately introduce no new implementation merely to preserve a chapter-to-commit rhythm.

---

## Architectural Evolution

The implementation roughly evolves through these pressures:

| Chapter | Pressure                                       | What Emerges                     |
| ------- | ---------------------------------------------- | -------------------------------- |
| 3       | Where should the first business rule live?     | Domain model + TDD               |
| 4       | A primitive stops being sufficient             | Value Object                     |
| 5       | Data becomes a business concept                | Richer Domain modeling           |
| 6       | Someone must protect the rules                 | Aggregate responsibility         |
| 7       | Booleans cannot express the process            | Explicit business state          |
| 8       | Identity matters across time                   | Entity identity                  |
| 9       | A complete operation needs coordination        | Application use case             |
| 10      | Orders must survive memory                     | Repository port                  |
| 11      | Real persistence is required                   | Django ORM adapter               |
| 12      | Loading history is not business behavior       | Read responsibility              |
| 13      | In-memory success is insufficient              | Real persistence testing         |
| 14      | Several changes belong together                | Unit of Work                     |
| 15      | Something happened in the business             | Domain Event                     |
| 16      | Multiple things care about the fact            | Event-driven reactions           |
| 17      | Events and transactions fail differently       | Transaction-aware event handling |
| 18      | External clients need access                   | Django/DRF HTTP adapter          |
| 19      | Domain errors do not speak HTTP                | Error translation                |
| 20      | Clients need information, not behavior         | Query/read path                  |
| 21      | One Order becomes many                         | Collection-oriented reads        |
| 22      | Correct reads become slow                      | Read-side optimization           |
| 23      | Secondary work should not block the customer   | EventPublisher                   |
| 24      | Another process must receive the fact          | Redis + EventReceiver            |
| 25      | Transport does not define meaning              | Application dispatch             |
| 26      | Historical facts need their own representation | Historical read boundary         |
| 27      | Reads and writes have diverged                 | Explicit Commands and Queries    |
| 28      | Concrete dependencies need construction        | Composition Root                 |
| 29      | Working pieces may not form a working system   | System-level architectural proof |
| 30      | Django is claimed to be an adapter             | Flask replacement experiment     |

This table should not be read as an architecture checklist.

It is a map of the pressures that caused the final architecture to emerge.

---

## Architecture Journal

Architectural decisions are documented in:

```text
docs/architecture-journal/
```

The journal currently contains **28 decision records**, beginning with:

```text
001-empty-order-placement.md
```

and ending with:

```text
028-we-said-django-was-an-adapter-prove-it.md
```

The journal records **architectural decisions, not book chapters**. An entry exists when the implementation creates a meaningful architectural decision worth preserving: the pressure, the decision, relevant alternatives, and why the selected approach earned its place.

This is why the journal stops at decision 028 even though the book contains 32 chapters. Chapters 31 and 32 are retrospective: they examine the architecture and the decision-making process rather than introducing implementation solely to keep the journal numbering aligned with the manuscript.

The different artifacts therefore answer different questions:

```text
Code
 └── What exists?

Tests
 └── What behavior and architectural claims can we demonstrate?

Architecture Journal
 └── Why was this decision made?

Git history
 └── How did the system change to get here?

Book
 └── What pressure made the decision necessary?
```

Together, they make the architecture reconstructable rather than presenting only its final state.

---

## What NovaTrade Deliberately Does Not Include

The final implementation intentionally does not add infrastructure or abstractions merely because they are common in production architectures.

For example, the project does not introduce a generic dependency-injection container simply because composition exists. It does not introduce a command bus merely because commands exist. It does not require a generic Domain Event base hierarchy merely because Domain Events exist.

Likewise, crossing a process boundary does not automatically cause NovaTrade to introduce every possible messaging concern or worker technology.

These omissions are intentional.

They reflect the same rule used throughout the implementation:

> **Complexity has to earn its place.**

A real production system may eventually require many of those capabilities. NovaTrade introduces them only when the demonstrated requirements justify them.

---

## Relationship to the Book

This repository is the executable companion to:

**_Building Software Around the Business — Not Around the Framework_**

The book explains the conversations, pressures, failed tests, trade-offs, and reasoning that caused the architecture to evolve.

The repository lets you inspect the implementation itself.

They are intended to complement each other:

```text
Book
 └── Why did this decision become necessary?

Repository
 └── What did that decision look like in executable code?

Git history
 └── What did the system look like before and after it?

Tests
 └── What evidence supports the behavior and architectural claims?
```

The final repository should therefore not be treated as a template to copy into a new application.

The more important lesson is the decision-making process that produced it.

---

## Core Principles

NovaTrade ends with three principles that summarize the implementation journey:

> ### No pattern without pressure.
>
> Introduce an architectural pattern when a concrete problem gives it a reason to exist.

> ### No infrastructure without a requirement.
>
> Add technology because the system needs a capability, not because the technology commonly appears in architecture diagrams.

> ### No architectural claim without proof.
>
> When an important architectural property matters, look for evidence that can challenge the claim.

The goal is not to avoid architecture.

The goal is to let the architecture become a record of responsible decisions.

---

## Author

**Olivier Lowe**

Software Developer focused on Python, Django, backend architecture, Domain-Driven Design, Test-Driven Development, and building software around business concepts rather than frameworks.
