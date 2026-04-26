# mirador-service-python

<sub>[English](README.md) · **Français**</sub>

[![pipeline](https://gitlab.com/mirador1/mirador-service-python/badges/main/pipeline.svg)](https://gitlab.com/mirador1/mirador-service-python/-/pipelines)
[![coverage](https://img.shields.io/badge/coverage-90.21%25-success)](https://gitlab.com/mirador1/mirador-service-python/-/pipelines)
[![Python 3.14](https://img.shields.io/badge/Python-3.14_+_3.13_3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
![SLO 99.5%](https://img.shields.io/badge/SLO-99.5%25_+_burn_rate-2D7FF9)
![mypy strict](https://img.shields.io/badge/mypy-strict-blue)

## Ce que ce projet démontre

Miroir Python de [`mirador-service-java`](https://gitlab.com/mirador1/mirador-service-java) —
mêmes préoccupations backend industrielles, exprimées dans la stack Python moderne :

- **Pipeline d'onboarding client industriel** (registration → validation → enrichissement
  externe via JSONPlaceholder + Ollama LLM → événements d'audit Kafka → suivi d'état →
  endpoints de diagnostic d'incident) — pas une démo CRUD.
- **Discipline de typage émulant Java** : `mypy --strict` + Pydantic v2 + `Final` /
  `Literal` / `TypeAlias` (PEP 695) partout ; **127 tests unitaires**, **couverture 90.21%**
  avec gate bloquant `--cov-fail-under=90` ; **8 tests property-based hypothesis** ;
  **import-linter** = ArchUnit pour Python.
- **Même observabilité** : OpenTelemetry (traces + logs + métriques) → stack LGTM,
  exporter starlette-prometheus, **3 SLOs définis-as-code via Sloth** avec alerting
  multi-window multi-burn-rate (Google SRE Workbook).
- **Même supply chain sécurité** : JWT (pyjwt) + bcrypt 5.x rotation, **gate CVE pip-audit**
  (3 CVEs corrigés pendant le dev), `gitleaks`, exit-tickets datés `--ignore-vuln`.
- **Même discipline CI** : GitLab CI exclusivement, runner group-level, conventional-commits,
  hooks lefthook 3-niveaux, ruleset ruff complet, Docker multi-arch via buildx.

La cible Python est **3.14 (branche par défaut)** — exploration de la stack la plus récente —
mais la matrice de compatibilité en CI compile + teste vert sur **3.12 + 3.13** depuis le même
code. Cible production conservatrice = 3.12 (le plus ancien avec PEP 695 `type` keyword +
ergonomie `Final` / `Literal`).

Voir [ADR-0007 — Pratiques Python industrielles](docs/adr/0007-industrial-python-best-practices.md)
pour la baseline de 13 décisions + [documentation SLO/SLA](docs/slo/).

## TL;DR pour les recruteurs (lecture 60 sec)

- **Démonstrateur polyrepo** : implémentation Python du même backend industriel servi par
  [`mirador-service-java`](https://gitlab.com/mirador1/mirador-service-java). Infra +
  observabilité + templates CI partagés via le submodule git
  [`mirador-service-shared`](https://gitlab.com/mirador1/mirador-service-shared).
- **mypy --strict sur 41 fichiers source** : Final / Literal / TypeAlias / aliases PEP 695,
  pas d'Any implicite, pas de defs non typées.
- **Couverture 90.21%** avec gate dur `--cov-fail-under=90` ; 127 tests unitaires + property-based
  hypothesis + 5 tests d'intégration kafka_client via testcontainers.
- **SLO/SLA-as-code** via Sloth : 3 SLOs (availability 99% / latency p99 < 500ms /
  enrichment 99.5%) sur 30j + alerting multi-burn-rate + dashboard Grafana.
- **Gate dur pip-audit** : 3 CVEs détectées + corrigées pendant le dev (pytest 9.0.3,
  fastapi 0.136.1, starlette 1.0.0).

## Pile technique

| Couche | Technologie | Équivalent Java |
|---|---|---|
| Framework web | **FastAPI** 0.115 | Spring Boot 4 Web MVC |
| DTO + validation | **Pydantic** v2.11 | Jackson + Bean Validation |
| ORM | **SQLAlchemy** 2.0 async | Spring Data JPA / Hibernate |
| Migrations | **Alembic** 1.14 | Flyway |
| Auth JWT | **pyjwt** + **bcrypt** 5.x | Spring Security + jjwt |
| Kafka | **aiokafka** 0.12 | Spring Kafka |
| Redis | **redis-py** 5.2 (asyncio) | Spring Data Redis |
| Observabilité | **OpenTelemetry SDK** + Prometheus | Micrometer + OTel SDK |
| Logging | **structlog** | Logback + structured logging |
| Rate limiting | **slowapi** | bucket4j |
| Cron | **APScheduler** | @Scheduled |
| Gestionnaire de paquets | **uv** | Maven |
| Tests | **pytest** + **pytest-asyncio** | JUnit 5 + Mockito |
| Lint / Format | **ruff** + **mypy** | Checkstyle + SpotBugs + PMD |
| Tests d'archi | **import-linter** | ArchUnit |
| Tests conteneurs | **testcontainers-python** | Testcontainers |
| Docker | multi-stage + uvicorn | multi-stage + Spring Boot |

## Démarrage rapide

```bash
# Installer les dépendances
uv sync --all-extras

# Lancer le serveur dev (hot reload)
uv run mirador-service

# Ou avec uvicorn explicite
uv run uvicorn mirador_service.app:app --reload --port 8080

# Lancer les tests
uv run pytest

# Lint + vérification de types
uv run ruff check src tests
uv run mypy src

# Démo complète (postgres + redis + kafka + LGTM + app)
bin/demo-up.sh
```

## Structure du projet

```
src/mirador_service/
  api/            # Routers FastAPI (= controllers Spring)
  auth/           # JWT + utilisateur injecté par dépendance (= Spring Security)
  customer/       # Domaine Customer (CRUD + RecentCustomerBuffer)
  integration/    # Services externes (TodoService, BioService stubs)
  messaging/      # Producers/consumers Kafka
  observability/  # Setup OTel + métriques custom
  middleware/     # CORS + Prometheus + SlowAPI rate-limit + structlog + request-id
  config/         # Réglages Pydantic (= application.yml)
  app.py          # Factory FastAPI + lifespan + middleware

tests/
  unit/           # pytest pur, deps mockées
  integration/    # backed par testcontainers (postgres, kafka, redis)

alembic/          # Migrations DB (= Flyway)
infra/            # docker-compose, postgres init, stack observabilité
infra/shared/     # Submodule mirador-service-shared (dev-stack + CI templates + ...)
infra/k8s/        # Manifests Kubernetes (Deployment + Service + HPA + PDB)
docs/             # Documentation mkdocs (autodoc API + ADRs + ops)
docs/adr/         # Architecture Decision Records (6 ADRs)
bin/              # Scripts d'ops (run.sh, demo-up.sh, etc.)
```

## Endpoints (miroir du service Java)

- `GET /customers` — liste paginée (dispatch v1 / v2 via `X-API-Version`)
- `POST /customers` — création + publication CustomerCreatedEvent (Kafka FAF)
- `GET /customers/{id}` — lecture
- `PUT /customers/{id}` — remplacement
- `PATCH /customers/{id}` — mise à jour partielle
- `DELETE /customers/{id}` — suppression
- `GET /customers/recent` — 10 derniers depuis le ring buffer Redis
- `GET /customers/{id}/audit` — trace d'audit synthétique
- `GET /customers/{id}/enrich` — enrichissement Kafka request-reply
- `GET /customers/{id}/todos` — JSONPlaceholder + retry tenacity
- `GET /customers/diagnostic/slow-query` — induit une requête lente (Tempo)
- `GET /customers/diagnostic/db-failure` — induit une erreur 500 (Loki)
- `GET /customers/diagnostic/kafka-timeout` — induit un 504 (Problem+JSON)
- `POST /auth/login` — émission JWT
- `POST /auth/refresh` — rotation refresh token
- `GET /auth/me` — claims utilisateur courant
- `GET /actuator/health` — composite (DB + Redis + Kafka)
- `GET /actuator/health/{liveness,readiness}` — sondes k8s
- `GET /actuator/info` — métadonnées runtime
- `GET /actuator/prometheus` — endpoint scrape métriques
- `GET /actuator/quality` — signaux qualité de code agrégés

## Philosophie compat

Comme le miroir Java — Python 3.14 par défaut, support Python 3.12/3.13 via
matrix CI informationnelle. Python 3.11 abandonné 2026-04-25 (EOL 2027-10).

## Projets sœurs

- [`../mirador-service-java`](../mirador-service-java) — backend Java/Spring Boot 4 (canonique)
- [`../../js/mirador-ui`](../../js/mirador-ui) — frontend Angular 21 (fonctionne contre l'un ou l'autre backend)
- [`../mirador-service-shared`](../mirador-service-shared) — infrastructure partagée (dev-stack docker-compose + templates CI + scripts budget + ADRs cross-cutting)

## Documentation

- 📚 Site mkdocs : https://mirador1.gitlab.io/mirador-service-python/ (publié sur GitLab Pages à chaque push main)
- 📋 ADRs : `docs/adr/` (6 records — choix de stack, auth, Kafka, observabilité, settings, logging)
- 🔬 Java sibling : https://gitlab.com/mirador1/mirador-service-java
- 🌐 Mirroir GitHub : https://github.com/mirador1/mirador-service-python

## Licence

MIT
