# mirador-service-python

Miroir Python de [`mirador-service-java`](https://gitlab.com/mirador1/mirador-service-java)
— démo de service client construite avec FastAPI + Pydantic v2 + SQLAlchemy 2.x async.

**Même philosophie que l'original Java** : projet de démo de niveau industriel
montrant l'observabilité moderne (OpenTelemetry, Prometheus), la sécurité
(authentification JWT), les patterns event-driven (Kafka request-reply),
le caching (Redis) et la discipline CI/CD (pipelines GitLab, ADRs,
conventional commits, dépendances figées).

> 🇬🇧 English version : [README.md](README.md)

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
