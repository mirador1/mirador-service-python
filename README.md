# mirador-service-python

<sub>**English** · [Français](README.fr.md)</sub>

[![pipeline](https://gitlab.com/mirador1/mirador-service-python/badges/main/pipeline.svg)](https://gitlab.com/mirador1/mirador-service-python/-/pipelines)
[![coverage](https://img.shields.io/badge/coverage-90.21%25-success)](https://gitlab.com/mirador1/mirador-service-python/-/pipelines)
[![Python 3.14](https://img.shields.io/badge/Python-3.14_+_3.13_3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
![SLO 99.5%](https://img.shields.io/badge/SLO-99.5%25_+_burn_rate-2D7FF9)
![mypy strict](https://img.shields.io/badge/mypy-strict-blue)

## What this project proves

Python mirror of [`mirador-service-java`](https://gitlab.com/mirador1/mirador-service-java) —
same industrial-grade backend concerns, expressed in the modern Python stack :

- **Industrial Customer onboarding pipeline** (registration → validation → external
  enrichment via JSONPlaceholder + Ollama LLM → Kafka audit events → state
  tracking → diagnostic incident endpoints) — not a CRUD demo.
- **Type discipline emulating Java** : `mypy --strict` + Pydantic v2 + `Final` /
  `Literal` / `TypeAlias` (PEP 695) decorators everywhere ; **127 unit tests**,
  **coverage 90.21%** with `--cov-fail-under=90` blocking gate ; **8 hypothesis
  property-based tests** ; **import-linter** = Python's ArchUnit.
- **Same observability** : OpenTelemetry (traces + logs + metrics) → LGTM stack,
  starlette-prometheus exporter, **3 SLOs defined-as-code via Sloth** with
  multi-window multi-burn-rate alerting (Google SRE Workbook).
- **Same security supply chain** : JWT (pyjwt) + bcrypt 5.x rotation, **pip-audit
  CVE gate** (3 CVEs fixed during dev), `gitleaks`, dated `--ignore-vuln` exit-tickets.
- **Same CI discipline** : GitLab CI exclusively, group-level runner,
  conventional-commits, lefthook 3-tier hooks, ruff comprehensive ruleset,
  multi-arch Docker via buildx.

The Python target is **3.14 (default branch)** — exploring the latest stack —
but the compat matrix in CI also builds + tests green on **3.12 + 3.13** from
the same source. Conservative production target = 3.12 (oldest with PEP 695
`type` keyword + `Final` / `Literal` ergonomics).

See [ADR-0007 — Industrial Python practices](docs/adr/0007-industrial-python-best-practices.md)
for the 13-decision baseline + [SLO/SLA documentation](docs/slo/).

## TL;DR for hiring managers (60 sec read)

- **Polyrepo demonstrator** : Python implementation of the same industrial backend
  served by [`mirador-service-java`](https://gitlab.com/mirador1/mirador-service-java).
  Shared infra + observability + CI templates via [`mirador-service-shared`](https://gitlab.com/mirador1/mirador-service-shared)
  git submodule (see [polyrepo-vs-monorepo ADR](https://gitlab.com/mirador1/mirador-service-shared/-/blob/main/docs/adr/0057-polyrepo-vs-monorepo.md)).
- **mypy --strict on 41 source files** : Final / Literal / TypeAlias / PEP 695
  type aliases, no implicit Any, no untyped defs.
- **Coverage 90.21%** with `--cov-fail-under=90` hard gate ; 127 unit tests +
  hypothesis property-based + 5 kafka_client integration tests via testcontainers.
- **SLO/SLA-as-code** via Sloth : 3 SLOs (availability 99% / latency p99 < 500ms /
  enrichment 99.5%) over 30d + multi-burn-rate alerting + Grafana dashboard.
- **pip-audit hard gate** : 3 CVEs caught + fixed during dev (pytest 9.0.3,
  fastapi 0.136.1, starlette 1.0.0).

## What this proves for a senior backend architect

| Concern | What this repo demonstrates | Why it matters in production |
|---|---|---|
| **Type discipline** | `mypy --strict` on 41 files ; PEP 695 `type` aliases ; `Final[T]` constants ; `Literal["access","refresh"]` for token-type narrowing ; 5 ADRs (0008-0012) document the discipline. | Python's runtime-only typing gets compile-time-equivalent guarantees ; refactors stay safe. |
| **Async-first architecture** | Every I/O path is `async def` ; SQLAlchemy 2.x async + asyncpg + aiokafka + redis-py async + httpx.AsyncClient ; ContextVar correlation propagates across coroutines. (ADR-0008) | One event loop per worker handles 100s of concurrent requests vs ~10 on sync workers — same hardware, 10× throughput. |
| **Test rigor** | 127 unit tests + 8 hypothesis property-based (found 2 real bugs during authoring) + 5 kafka_client integration tests via testcontainers + pytest-benchmark on hot paths (JWT 9µs, bcrypt 280ms). Coverage 90.21% with `--cov-fail-under=90` blocking gate. | Coverage isn't pretend — the gate fails CI ; property-based catches edge cases example-tests miss. |
| **Architectural boundaries** | `import-linter` enforces 4 contracts : config-leaf, db↔kafka independence, integration adapters independence, observability-leaf. CI fails on violation. (ADR-0007 §5) | Python's import flexibility = drift risk ; tooling enforcement > reviewer goodwill. |
| **Security supply chain** | JWT (pyjwt) + bcrypt 5.x rotation, **pip-audit hard gate** (3 CVEs caught during dev), gitleaks secret scan, dated `--ignore-vuln` exit-tickets, OWASP rules via ruff bandit. | Pinning is half — knowing when a pinned version becomes vulnerable is the other half. |
| **Observability** | OTel SDK → Collector → LGTM ; structlog JSON logs ; starlette-prometheus metrics ; **3 SLOs as code via Sloth** with multi-window multi-burn-rate alerting (Google SRE Workbook). (ADR-0012) | "Are we within contract this month ?" is an objective question with a Grafana dashboard. |
| **Tooling modernization** | `uv` replaces pip + setuptools + virtualenv + pyenv (5-10× faster, cross-platform lockfile). PEP 695 type syntax. (ADR-0009) | Stays on the bleeding edge of Python tooling ; demonstrates ability to evaluate + adopt new ecosystem leaders. |
| **Java parity** | Same 3 SLOs, same Kafka contract, same security baseline as the Java sibling. Shared submodule (`mirador-service-shared`) enforces the common floor. | Demonstrates ability to keep multiple stack implementations consistent without monorepo lock-in. |

## Tech stack

| Layer | Technology | Mirrors Java's |
|---|---|---|
| Web framework | **FastAPI** 0.136 | Spring Boot 4 Web MVC |
| DTO + validation | **Pydantic** v2.11 | Jackson + Bean Validation |
| ORM | **SQLAlchemy** 2.0 async | Spring Data JPA / Hibernate |
| Migrations | **Alembic** 1.14 | Flyway |
| JWT auth | **pyjwt** + **bcrypt** 5.x | Spring Security + jjwt |
| Kafka | **aiokafka** 0.13 | Spring Kafka |
| Redis | **redis-py** 5.2 (asyncio) | Spring Data Redis |
| Observability | **OpenTelemetry SDK** + Prometheus | Micrometer + OTel SDK |
| **SLO/SLA-as-code** | **Sloth** + multi-burn-rate | Sloth (mirror) |
| Logging | **structlog** | Logback + structured logging |
| Rate limiting | **slowapi** | bucket4j |
| Package manager | **uv** (Astral) | Maven |
| Test | **pytest** + **pytest-asyncio** + **hypothesis** | JUnit 5 + Mockito |
| Property-based | **hypothesis** | jqwik |
| Benchmarks | **pytest-benchmark** | JMH |
| Lint / Format | **ruff** + **mypy** strict | Checkstyle + SpotBugs + PMD |
| Arch tests | **import-linter** (4 contracts) | ArchUnit |
| CVE scan | **pip-audit** | OWASP Dependency-Check |
| Container tests | **testcontainers-python** | Testcontainers |
| Docker | multi-stage + uvicorn (Py 3.14 slim) | multi-stage + Spring Boot |

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
- `POST /mcp/` — Model Context Protocol streamable-http transport (see below)

## AI integration via MCP

Mirrors the Java sibling's [ADR-0062](https://gitlab.com/mirador1/mirador-service-java/-/blob/main/docs/adr/0062-mcp-server-tool-exposure-per-method.md)
— Mirador exposes an in-process [Model Context Protocol](https://modelcontextprotocol.io/)
server at `/mcp/`. An LLM client (Claude Desktop, `claude mcp add`,
the MCP Inspector) connects with the same JWT the REST API uses and
gets a typed catalogue of 14 tools without any new HTTP plumbing.

**Architectural constraint** : the backend stays infrastructure-agnostic
— ZERO HTTP clients to Loki / Mimir / Grafana / GitLab / GitHub /
kubectl in the FastAPI process. Only what the backend ALREADY produces
in-process : Python `logging` ring buffer, prometheus_client REGISTRY,
FastAPI's auto-OpenAPI, and the Order/Product/Customer domain.

External infra MCPs (Loki tail, Mimir query, Grafana panel render)
live OUTSIDE the codebase ; each Claude session adds them
independently via `claude mcp add`. See ADR-0062 §"External infra MCP
servers" for the produces-vs-accesses decision rule.

### 14 tools

| Domain (7) | Backend-local observability (7) |
|---|---|
| `list_recent_orders` | `tail_logs` |
| `get_order_by_id` | `get_metrics` |
| `create_order` (idempotent) | `get_health` |
| `cancel_order` | `get_health_detail` (admin) |
| `find_low_stock_products` | `get_actuator_env` (redacted) |
| `get_customer_360` | `get_actuator_info` |
| `trigger_chaos_experiment` (admin) | `get_openapi_spec` |

Returns are typed Pydantic v2 DTOs (frozen=True) ; ORM entities
NEVER reach the LLM. Decimal stays Decimal (NUMERIC(12,2) precision
preserved). Each tool call writes a structured audit log line
(action=`MCP_TOOL_CALL`, args hashed to 8-char SHA-256 prefix).

### 60-second demo

```bash
# 1. Start the service
uv run mirador-service                # or: docker compose up

# 2. Mint a JWT
TOKEN=$(curl -s -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq -r .access_token)

# 3. Initialize an MCP session
curl -s -X POST http://localhost:8080/mcp/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{
       "protocolVersion":"2025-06-18","capabilities":{},
       "clientInfo":{"name":"demo","version":"0"}}}'

# 4. Call a tool
curl -s -X POST http://localhost:8080/mcp/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{
       "name":"get_actuator_info","arguments":{}}}'
```

Or wire the service to your local Claude Desktop / Claude CLI :
```
claude mcp add --transport http mirador http://localhost:8080/mcp/
```

### Auth

The MCP endpoint goes through the same `decode_token()` path as REST
(see `mirador_service/auth/jwt.py`). `get_health_detail` and
`trigger_chaos_experiment` are admin-only ; all other tools accept
any authenticated user. Admin tokens carry both `ROLE_USER` and
`ROLE_ADMIN` scopes (admin = superset).

## Compat philosophy

Same as Java mirror — Python 3.13 default, support Python 3.11/3.12 via
overlay shims if needed.

## Sibling projects

- [`../mirador-service`](../mirador-service) — Java/Spring Boot 4 backend (canonical)
- [`../../js/mirador-ui`](../../js/mirador-ui) — Angular 21 frontend (works against either backend)

## License

MIT
