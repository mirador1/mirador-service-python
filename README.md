# mirador-service-python

Python mirror of [`mirador-service`](https://gitlab.com/mirador1/mirador-service)
— customer service demo built with FastAPI + Pydantic v2 + SQLAlchemy 2.x async.

**Same philosophy as the Java original** : industrial-grade demo project showing
modern observability (OpenTelemetry, Prometheus), security (JWT auth), event-
driven patterns (Kafka request-reply), caching (Redis), and CI/CD discipline
(GitLab pipelines, ADRs, conventional commits, pinned dependencies).

## Tech stack

| Layer | Technology | Mirrors Java's |
|---|---|---|
| Web framework | **FastAPI** 0.115 | Spring Boot 4 Web MVC |
| DTO + validation | **Pydantic** v2.10 | Jackson + Bean Validation |
| ORM | **SQLAlchemy** 2.0 async | Spring Data JPA / Hibernate |
| Migrations | **Alembic** 1.14 | Flyway |
| JWT auth | **python-jose** + **passlib** | Spring Security + jjwt |
| Kafka | **aiokafka** 0.12 | Spring Kafka |
| Redis | **redis-py** 5.2 (asyncio) | Spring Data Redis |
| Observability | **OpenTelemetry SDK** + Prometheus | Micrometer + OTel SDK |
| Logging | **structlog** | Logback + structured logging |
| Rate limiting | **slowapi** | bucket4j |
| Package manager | **uv** | Maven |
| Test | **pytest** + **pytest-asyncio** | JUnit 5 + Mockito |
| Lint / Format | **ruff** + **mypy** | Checkstyle + SpotBugs + PMD |
| Arch tests | **import-linter** | ArchUnit |
| Container tests | **testcontainers-python** | Testcontainers |
| Docker | multi-stage + uvicorn | multi-stage + Spring Boot |

## Quickstart

```bash
# Install dependencies
uv sync --all-extras

# Run dev server (hot reload)
uv run mirador-service

# Or with explicit uvicorn
uv run uvicorn mirador_service.app:app --reload --port 8080

# Run tests
uv run pytest

# Lint + type check
uv run ruff check src tests
uv run mypy src
```

## Project layout

```
src/mirador_service/
  api/            # FastAPI routers (= Spring controllers)
  auth/           # JWT + dependency-injected user (= Spring Security)
  customer/       # Customer domain (CRUD + RecentCustomerBuffer)
  integration/   # External services (BioService, TodoService stubs)
  messaging/     # Kafka producers/consumers
  observability/ # OTel setup + custom metrics
  config/         # Pydantic settings (= application.yml)
  app.py          # FastAPI app factory + lifespan + middleware
  main.py         # Entry point (uvicorn / gunicorn)

tests/
  unit/           # pure pytest, mocked deps
  integration/    # testcontainers-backed (postgres, kafka, redis)

alembic/          # DB migrations (= Flyway)
infra/            # docker-compose, postgres init, observability stack
docs/adr/         # Architecture Decision Records
bin/              # ops scripts (run.sh, demo-up, etc.)
```

## Endpoints (mirror of Java service)

- `GET /customers` — paginated list (v1 / v2 dispatch via `X-API-Version`)
- `POST /customers` — create
- `GET /customers/{id}` — read
- `PUT /customers/{id}` — replace
- `PATCH /customers/{id}` — partial update
- `DELETE /customers/{id}` — delete
- `GET /customers/recent` — last 10 from Redis ring buffer
- `GET /customers/{id}/audit` — audit trail
- `GET /customers/{id}/enrich` — Kafka request-reply
- `POST /auth/login` — JWT issue
- `POST /auth/refresh` — refresh token rotation
- `GET /actuator/health` — liveness + readiness composite
- `GET /actuator/prometheus` — metrics scrape endpoint
- `GET /actuator/info` — build + git info

## Compat philosophy

Same as Java mirror — Python 3.13 default, support Python 3.11/3.12 via
overlay shims if needed.

## Sibling projects

- [`../mirador-service`](../mirador-service) — Java/Spring Boot 4 backend (canonical)
- [`../../js/mirador-ui`](../../js/mirador-ui) — Angular 21 frontend (works against either backend)

## License

MIT
