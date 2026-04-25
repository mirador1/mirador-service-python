# TASKS — mirador-service-python

Source of truth for pending work across sessions. Read at session start ;
update on every task change ; commit + push immediately so the next session
sees current state.

## ✅ Done — initial scaffolding waves (2026-04-25)

- Étape 1 : pyproject + Dockerfile + .gitlab-ci modular + scaffolding
- Étape 2 : customer CRUD + 12 tests + ADR-0001
- Étape 3 : actuator (`/health`, `/info`, `/prometheus`) + Redis recent buffer + 12 tests
- Étape 4 : `GET /customers/{id}/enrich` Kafka request-reply broker + 10 tests
- Étape 5 : OpenTelemetry SDK + auto-instrumentation + 3 tests + ADR-0003
- Étape 6 : Alembic V1 migration (customer + app_user + refresh_token) + 3 tests + workflow doc
- Étape 7 : docker-compose dev stack + bin/run.sh + bin/demo-up.sh + bin/demo-down.sh
- Étape 8 : middleware (structlog + request-id + CORS + slowapi) + ADRs 0002 (auth) / 0004 (Kafka)
- Étape 9 : coverage gate 65% → 80% (baseline 84% via greenlet hook + 16 new tests)

Stable checkpoint pending (no tag yet — needs first green main pipeline post-merge).

## 🔄 Open — Étape 10+ (next session)

### High value, low effort

- [ ] **Stable-v0.1.0 tag** → marks the "minimum viable Python mirror" baseline.
      Wait for the first green main pipeline AFTER dev → main merge, THEN tag.
      Per `~/.claude/CLAUDE.md` rule "Tag every green stability checkpoint".

- [ ] **Auto-merge dev → main** → currently no MR exists.
      Run `glab mr create --fill --target-branch main --remove-source-branch=false`,
      then `glab mr merge <id> --auto-merge --squash=false --remove-source-branch=false`.
      Verify CI is configured to run on MR + main + can actually deploy.

- [x] **Add `service.namespace` resource attribute** in `observability/otel.py` so
      Tempo/Mimir can group Python + Java services under the same namespace
      (`mirador`). DONE 2026-04-25 in commit (post-tasks-md).

- [x] **Wire `/auth/me`** endpoint returning `{"username", "role"}` from
      `current_user`. DONE 2026-04-25 + 3 tests (401 missing, 200 valid,
      401 refresh-on-access).

- [ ] **Add `/customers/{id}/bio`** + **/customers/{id}/todos** parity with the
      Java side : Bio = Ollama LLM call (Resilience4j-equivalent retry via
      `tenacity`), Todos = JSONPlaceholder external API (also tenacity +
      fallback). Mirrors Java's `CustomerEnrichmentController` triplet.

### Higher value, more effort

- [ ] **Étape 10 — testcontainers integration tests** :
      - Postgres : real `db/base.py` engine lifecycle + repository CRUD
        against actual SQL behaviour (server defaults, JSONB, UNIQUE
        violations on insert).
      - Kafka : real producer + consumer round-trip, verify trace
        propagation in headers, verify rebalance on restart.
      - LGTM container : verify OTel spans actually arrive in Tempo
        (HTTP query to `localhost:3200/api/traces?service=mirador-service-python`).
      Closes the remaining coverage gaps (`kafka_client.py` 24%,
      `observability/otel.py` 44%, `db/base.py` 39%).

- [ ] **Étape 11 — Refresh token cleanup job** : APScheduler async cron that
      deletes revoked + expired entries from `refresh_token` daily at 03:00.
      ADR-0002 flagged this as TODO. Otherwise the table grows unbounded.

- [ ] **Étape 12 — Rate-limit Redis backend** : current SlowAPI uses
      in-memory store ; per-replica counters drift in a multi-pod deploy.
      Switch to `slowapi.Limiter(storage_uri="redis://...")`. Same Redis
      already wired for the recent-customer buffer.

- [ ] **Étape 13 — Multi-stage Docker build optimisation** : current Dockerfile
      uses uv. Verify final image size < 200 MB (prod target) ; if larger,
      audit deps + use `--no-install-package` for build-only deps.

- [ ] **Étape 14 — k8s manifests** under `infra/k8s/` : Deployment + Service
      + HPA + ConfigMap (.env-derived) + Secret stub. Mirror the Java
      side's `infra/k8s/`. Probes wire to `/actuator/health/liveness` +
      `/actuator/health/readiness`.

- [ ] **Étape 15 — GitLab CI compat matrix completion** : currently runs Python
      3.11/3.12/3.14 in parallel. Add a Postgres service container so
      integration tests run in CI too. Add a `sonarqube` job pointing at
      the Sonar instance the Java side uses.

### Lower priority / nice-to-have

- [ ] **ADR-0005** : Pydantic v2 settings hierarchy (env > .env > defaults)
      — capture the `MIRADOR_DB__HOST` style with `__` nested delimiter +
      `lru_cache` singleton choice.

- [ ] **ADR-0006** : structlog over stdlib logging — capture the
      ProcessorFormatter trick that routes uvicorn / sqlalchemy / aiokafka
      logs through structlog so EVERY log line is JSON in prod.

- [ ] **README.fr.md** — French localised README (mirror UI repo pattern).

- [ ] **Replace `python-jose`** with `pyjwt` — python-jose has been semi-
      abandoned (last release 2022-12). pyjwt is actively maintained.
      Migration is straightforward (similar API). ADR + PR.

- [ ] **Replace `passlib`** with `argon2-cffi` or pure `bcrypt` (≥4.x) —
      passlib is also semi-abandoned, and the bcrypt 5.x compat issue
      forced a 3.2.2 pin. argon2-cffi is the modern recommendation.

## Format rules

- Each item : ☐ for open, ☑ for done, then **action → why** per
  `~/.claude/CLAUDE.md` "Every item — state what AND why" rule.
- Group by priority (high-value-low-effort, high-effort, nice-to-have).
- When ALL items shipped : delete this file + commit the deletion.
  Don't keep an empty TASKS.md.
