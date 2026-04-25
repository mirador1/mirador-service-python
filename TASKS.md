# TASKS — mirador-service-python

Open work only. Per `~/.claude/CLAUDE.md` rules : Python-only items
here ; done items removed (use `git tag -l` for history).

**⏸ PYTHON WORK PAUSED** per user 2026-04-25 — resume on signal.

---

## 🟡 High value, low effort

- ☐ **Stable-v0.1.0 tag** → first Python checkpoint after dev → main
  merge + green main pipeline. Per `~/.claude/CLAUDE.md` "Tag every
  green stability checkpoint".

- ☐ **Auto-merge dev → main** : `glab mr create --fill --target-branch main
  --remove-source-branch=false`, then `glab mr merge <id> --auto-merge
  --squash=false --remove-source-branch=false`.

- ☐ **`/customers/{id}/bio`** : Ollama LLM call + tenacity retry, mirror
  of Java side. Defer until docker-compose includes ollama service
  (Étape 7 stack doesn't yet).

---

## 🟡 Higher value, more effort

- ☐ **Étape 10 sub** :
  - LGTM container test : verify OTel spans actually reach Tempo
    (`http://localhost:3200/api/traces?service=mirador-service-python`).
  - GitLab CI `integration-tests` job : separate stage, parallel to
    lint + unit, with Docker-in-Docker service.
  - Run integration suite locally end-to-end (testcontainers needs
    Docker daemon + a kafka pull ~700 MB).

- ☐ **Étape 11 — Refresh token cleanup job** : APScheduler async cron
  deletes revoked + expired entries from `refresh_token` daily at 03:00.
  ADR-0002 flagged this. Otherwise table grows unbounded.

- ☐ **Étape 12 — Rate-limit Redis backend** : current SlowAPI uses
  in-memory store ; multi-pod replicas drift. Switch to
  `slowapi.Limiter(storage_uri="redis://...")`.

- ☐ **Étape 13 — Multi-stage Docker build optimisation** : verify final
  image size < 200 MB (prod target) ; audit deps if larger.

- ☐ **Étape 14 — k8s manifests** under `infra/k8s/` : Deployment +
  Service + HPA + ConfigMap (.env-derived) + Secret stub. Mirror Java
  side. Probes wire to `/actuator/health/{liveness,readiness}`.

- ☐ **Étape 15 — GitLab CI compat matrix completion** : add a Postgres
  service container so integration tests run in CI ; add a `sonarqube`
  job pointing at the Sonar instance Java uses.

---

## 🤔 À considérer

- 🟢 **README.fr.md** — French localised README (mirror UI repo pattern).

- 🟢 **Replace `python-jose`** with `pyjwt` — python-jose semi-abandoned
  (last release 2022-12). pyjwt actively maintained ; migration
  straightforward. ADR + PR.

- 🟢 **Replace `passlib`** with `argon2-cffi` or `bcrypt ≥ 4.x` — passlib
  semi-abandoned ; bcrypt 5.x compat issue forced 3.2.2 pin. argon2-cffi
  is the modern recommendation.
