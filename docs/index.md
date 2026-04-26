# Mirador Service Python

Python mirror of [`mirador-service-java`](https://gitlab.com/mirador1/mirador-service-java)
— FastAPI + Pydantic v2 + SQLAlchemy 2.x async + Kafka + Redis + OpenTelemetry +
**Sloth-defined SLOs**.

## What this proves

Industrial backend demonstrator focused on production-grade Python practices :

- **Type discipline emulating Java** : `mypy --strict` on 41 files, PEP 695
  `type` aliases, `Final[T]` constants, `Literal["access","refresh"]` token
  narrowing. Coverage 90.21% with `--cov-fail-under=90` blocking gate.
- **Async-first architecture** (ADR-0008) : every I/O path is `async def` ;
  100s of concurrent requests on a single uvicorn worker.
- **Observability + SLO/SLA-as-code** : 3 SLOs via Sloth, multi-window
  multi-burn-rate alerts, Grafana dashboard with error budget tracking.
- **Security supply chain** : pip-audit hard gate (3 CVEs caught + fixed
  during dev), JWT + bcrypt 5.x rotation, gitleaks.
- **Architectural boundaries** : import-linter enforces 4 contracts
  (config-leaf, db↔kafka indep, integration adapters indep, observability-leaf).

The default branch targets **Python 3.14**. The compat matrix in CI also
builds + tests green on **3.12 + 3.13** from the same source — conservative
production target = 3.12 (oldest with PEP 695 + ergonomic Final/Literal).

## Quick links

- 📚 [API Reference](reference/app.md) — auto-generated from docstrings
- 🏗 [Architecture overview](architecture/overview.md)
- 📋 [ADRs](architecture/adrs.md) (12 records — stack, auth, Kafka, observability, settings, logging, industrial practices, async-first, uv, SQLAlchemy, hypothesis, Sloth SLO)
- 📊 [SLO definitions](https://gitlab.com/mirador1/mirador-service-python/-/blob/main/docs/slo/slo.yaml) + [SLA promise](https://gitlab.com/mirador1/mirador-service-python/-/blob/main/docs/slo/sla.md)
- 📖 [Runbooks](https://gitlab.com/mirador1/mirador-service-python/-/tree/main/docs/runbooks)
- 🛠 [README](https://gitlab.com/mirador1/mirador-service-python/-/blob/main/README.md)
- 🔬 [Java sibling](https://gitlab.com/mirador1/mirador-service-java) | [UI](https://gitlab.com/mirador1/mirador-ui) | [shared infra](https://gitlab.com/mirador1/mirador-service-shared)

## Stack at a glance

| Layer | Technology | Mirrors Java's |
|---|---|---|
| Web framework | FastAPI 0.136 | Spring Boot 4 Web MVC |
| DTO + validation | Pydantic v2.11 | Jackson + Bean Validation |
| ORM | SQLAlchemy 2.0 async | Spring Data JPA |
| Migrations | Alembic 1.14 | Flyway |
| JWT auth | **pyjwt** + **bcrypt** 5.x | Spring Security + jjwt |
| Kafka | aiokafka 0.13 | Spring Kafka |
| Redis | redis-py 5.2 (asyncio) | Spring Data Redis |
| Observability | OpenTelemetry SDK + starlette-prometheus | Micrometer + OTel SDK |
| **SLO/SLA-as-code** | **Sloth** + multi-burn-rate | Sloth (mirror) |
| Logging | structlog | Logback structured |
| Rate limiting | slowapi + Redis backend | bucket4j |
| Cron | APScheduler | @Scheduled |
| Package manager | **uv** (Astral) | Maven |
| Test | pytest + pytest-asyncio + **hypothesis** + pytest-benchmark | JUnit 5 + Mockito + jqwik + JMH |
| Lint / Format | ruff + mypy --strict | Checkstyle + SpotBugs + PMD |
| Arch tests | **import-linter** (4 contracts) | ArchUnit |
| CVE scan | **pip-audit** | OWASP Dependency-Check |

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
