# TASKS — mirador-service-python

Open work only. Per `~/.claude/CLAUDE.md` rules : Python-only items
here ; done items removed (use `git tag -l` for history).

---

## 🚫 Blocked (waiting on upstream)

- 🟢 **Wire mutmut in CI** : mutmut 3.5.0 installed + configured
  (`[tool.mutmut]` targeting `src/mirador_service/auth/`), but mutmut
  walks parent filesystem on `run` and hits unreadable
  `/.VolumeIcon.icns` on macOS. Track [boxed/mutmut issues](https://github.com/boxed/mutmut/issues).
  When fixed : add a manual GitLab CI job `mutmut` at validate stage,
  run on-demand for crypto-touching MRs.

- 🟢 **Docker image alpine** : 412 MB → ~280 MB possible. Blocked :
  pydantic_core / cryptography / bcrypt have no musl wheels. Revisit
  when uv ships musl wheels for Rust-extension deps.

## 🤔 À considérer (lower priority)

- 🟢 **Flip integration-tests CI job to required** (`allow_failure:
  false`) : currently informational. Acceptance criterion : 5 consecutive
  green runs of `integration-tests` on main. The new
  `test_kafka_client_lifecycle.py` is the reference — once stable, gate.

- 🟢 **Flip pip-audit CVE gate to enforcing** : currently set as hard
  gate (no allow_failure) but only ignores `CVE-2026-3219` (pip
  bundled, no fix yet). Re-check monthly. Remove the `--ignore-vuln`
  flag once pip ships the patched version.

- 🟢 **Flip sonarcloud to required** (`allow_failure: false` →
  remove the line) : after first 5 green runs (TODO date 2026-05-25
  in `.gitlab-ci/quality.yml`).

- 🟢 **Migrate Java's `jvm.config` Comments rule to Python's
  `pytest.ini_options`** : adopt the same dated-TODO comment pattern
  for `allow_failure` shields once we have any.

## 📊 SLO/SLA backlog (post Quick wins ADR-0058)

Quick wins SHIPPED 2026-04-25 : 3 SLOs as code (Sloth) + multi-burn-rate
alerting + Grafana SLO dashboard + ADR-0058 + sla.md. Below = next iterations.

- 🟢 **Dashboard "SLO breakdown by endpoint"** : current dashboard shows
  service-wide SLO. Add a 2nd dashboard (or panel row) sliced by
  `path_template` to identify which endpoints contribute most to the
  budget burn. Useful when an SLO breach happens — answers "which
  endpoint is dragging us down ?".

- 🟢 **Chaos-driven SLO demo** : wire `/customers/diagnostic/slow-query`
  + `db-failure` + `kafka-timeout` to intentionally burn budget for
  demo purposes. A "demo mode" Grafana annotation that overlays the
  burn rate timeseries with the chaos test markers. Sells the
  observability story in 30 seconds.

- 🟢 **Runbook section "What to do when SLO breached"** :
  `docs/runbooks/slo-availability.md`, `slo-latency.md`, `slo-enrichment.md`
  (URLs already referenced in `slo.yaml` annotations). Each : symptoms,
  first investigation steps, common root causes, escalation path,
  rollback procedure. Currently empty — links 404 on Alertmanager.

- 🟢 **Latency heatmap par endpoint** : Grafana panel using histogram
  `_bucket` series, x=time × y=latency-bucket, color=request count.
  Shows tail-latency distribution in one glance — complement to p99
  SLO compliance.

- 🟢 **Apdex score dashboard** : add `Apdex(0.5s, 2s)` calculation to
  the SLO dashboard. Apdex = (satisfied + tolerating/2) / total.
  Single number that captures "user satisfaction" — easier to
  communicate to non-SRE stakeholders than 3 separate SLOs.

- 🟢 **Monthly SLO review meeting cadence** : document in
  `docs/slo/review-cadence.md`. What to bring (compliance %, top burn
  contributors, capacity changes, deploy correlation), who attends,
  what's the output (tighten/relax SLO, error budget policy update).
  Currently NOT documented — remove from `sla.md` claim or implement.

## 🎨 README polish (post 2026-04-25 review)

Captured from portfolio review session feedback :

- 🟢 **README.fr.md sync** : Python README.md got a major rewrite 2026-04-25
  (badges + TL;DR for hiring managers + Sloth/SLO badges + tech stack with
  hypothesis/pip-audit/Sloth + "Industrial Customer onboarding" reframing).
  The French version still reflects the old structure — sync needed.

- 🟢 **Add "What this proves for a senior backend architect" matrix** :
  Java README has it (8-row Concern × Demonstration × Production rationale).
  Python TL;DR exists but the full matrix doesn't — add the equivalent
  Python-specific table (mypy strict + cov 90% + hypothesis + import-linter
  + pip-audit + SLO + kafka_client integration tests).

- 🟢 **Mini-domain rename consideration** : same as Java side — narrative
  reframing in README done, code still uses `Customer*` classes. Defer.

- 🟢 **mkdocs landing page refresh** : `docs/index.md` should mirror the
  new README structure (TL;DR + senior architect matrix). Currently shows
  old "Customer service demo" framing.

## 🎯 Augmenter la surface fonctionnelle — nouvelles entités

☐ Mirror les nouvelles entités côté Python (parité OpenAPI obligatoire
avec Java — l'UI doit pouvoir basculer entre les 2 backends transparently).

**Scope final (validé utilisateur 2026-04-26)** : Pattern A (e-commerce) +
relation `User` extraite du Pattern B (SaaS rôles) :

- **`User`** — identité auth avec rôles (USER / ADMIN / MANAGER), `email`,
  `password_hash` (à factoriser avec l'auth JWT existante côté Customer
  si applicable). Linked to `Customer` via `customer_id` (le user
  représente un opérateur attaché à un Customer).
- **`Order`** — entité principale, DEUX FKs :
  - `customer_id` → `Customer` existant (le buyer / owner de la commande)
  - `created_by_user_id` → `User` (l'opérateur qui a créé la commande)
  - statut (PENDING / CONFIRMED / SHIPPED / CANCELLED), `total_amount` calculé
- **`Product`** — `name`, `description`, `unit_price`, `stock_quantity`
- **`OrderLine`** — jonction Order ↔ Product : `quantity`,
  `unit_price_at_order` (immutable, snapshot du prix au moment de la commande)

### Acceptance criteria

- [ ] Modèles SQLAlchemy 2.x async (`src/mirador_service/{user,order,product}/models.py`,
      feature-sliced)
- [ ] Migrations (suivre le pattern Alembic existant pour `Customer`)
- [ ] Pydantic v2 schemas request / response avec validation des rôles
      (`Literal['USER', 'ADMIN', 'MANAGER']`)
- [ ] FastAPI endpoints : full CRUD (`/users`, `/orders`, `/products`,
      `/orders/{id}/lines`) avec OpenAPI auto-spec
- [ ] **Auth refactor si applicable** : si `Customer` portait l'auth JWT,
      la déplacer vers `User` (rôles). Sinon ajouter le mécanisme.
- [ ] Coverage ≥ 90 % (cf. [ADR-0014](docs/adr/0014-coverage-floor-and-property-based-testing.md))
- [ ] Property tests Hypothesis sur invariants (total = Σ lignes, stock ≥ 0,
      OrderLine immutability, role transitions valides)
- [ ] Integration tests (Postgres async + redis ring buffer si applicable)
- [ ] Update `bin/dev/api-smoke.sh` avec les nouveaux endpoints
- [ ] CHANGELOG entry au prochain `stable-py-vX.Y.Z`

### Cross-repo coordination (cf. common ADR-0001 polyrepo)

OpenAPI contract DOIT correspondre exactement à
[Java's](https://gitlab.com/mirador1/mirador-service-java/-/blob/main/TASKS.md)
(même paths, même schemas, même response codes, même auth flow). UI doit
pouvoir basculer entre backends transparently. Acceptance partielle si
l'un des 3 repos n'a pas livré.
