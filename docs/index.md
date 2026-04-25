# Mirador Service Python

Python mirror of [`mirador-service`](https://gitlab.com/mirador1/mirador-service)
— FastAPI + Pydantic v2 + SQLAlchemy 2.x async + Kafka + Redis + OpenTelemetry.

## Quick links

- 📚 [API Reference](reference/app.md) — auto-generated from docstrings
- 🏗 [Architecture overview](architecture/overview.md)
- 📋 [ADRs](architecture/adrs.md) (6 records — stack choices, auth, Kafka, observability, settings, logging)
- 🛠 [README](https://gitlab.com/mirador1/mirador-service-python/-/blob/main/README.md)
- 🔬 [Java sibling](https://gitlab.com/mirador1/mirador-service)

## Stack at a glance

| Layer | Technology | Mirrors Java's |
|---|---|---|
| Web framework | FastAPI 0.115 | Spring Boot 4 Web MVC |
| DTO + validation | Pydantic v2.11 | Jackson + Bean Validation |
| ORM | SQLAlchemy 2.0 async | Spring Data JPA |
| Migrations | Alembic 1.14 | Flyway |
| JWT auth | python-jose + passlib | Spring Security + jjwt |
| Kafka | aiokafka 0.12 | Spring Kafka |
| Redis | redis-py 5.2 (asyncio) | Spring Data Redis |
| Observability | OpenTelemetry SDK | Micrometer + OTel SDK |
| Logging | structlog | Logback structured |
| Rate limiting | slowapi + Redis backend | bucket4j |
| Cron | APScheduler | @Scheduled |
| Package manager | uv | Maven |

## Endpoints

- `GET /customers` — paginated list (v1 / v2 dispatch via `X-API-Version`)
- `POST /customers` — create + publish CustomerCreatedEvent (Kafka FAF)
- `GET /customers/{id}` — read
- `PUT /customers/{id}` — replace
- `PATCH /customers/{id}` — partial update
- `DELETE /customers/{id}` — delete
- `GET /customers/recent` — last 10 from Redis ring buffer
- `GET /customers/{id}/audit` — synthetic audit trail
- `GET /customers/{id}/enrich` — Kafka request-reply enrichment
- `GET /customers/{id}/todos` — JSONPlaceholder + tenacity retry
- `GET /customers/diagnostic/slow-query` — induces slow span (Tempo)
- `GET /customers/diagnostic/db-failure` — induces 500 (Loki)
- `GET /customers/diagnostic/kafka-timeout` — induces 504 (Problem+JSON)
- `POST /auth/login` — JWT issue
- `POST /auth/refresh` — refresh token rotation
- `GET /auth/me` — current user claims
- `GET /actuator/health` — composite (DB + Redis + Kafka)
- `GET /actuator/health/{liveness,readiness}` — k8s probes
- `GET /actuator/info` — runtime metadata
- `GET /actuator/prometheus` — metrics scrape
- `GET /actuator/quality` — aggregated code-quality signals

## Quick start

```bash
# Install dependencies
uv sync --all-extras

# Run dev server (hot reload)
uv run mirador-service

# Or via the bin script
bin/run.sh

# Full demo (postgres + redis + kafka + LGTM + app)
bin/demo-up.sh
```

See [README](https://gitlab.com/mirador1/mirador-service-python/-/blob/main/README.md)
for the full setup guide.
