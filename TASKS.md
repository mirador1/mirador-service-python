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

## 🎯 Surface fonctionnelle — entités e-commerce

Foundation **shippée 2026-04-26** dans [stable-py-v0.6.4](https://gitlab.com/mirador1/mirador-service-python/-/tags/stable-py-v0.6.4) :
- ✅ Alembic 0002 (`product`), 0003 (`orders`), 0004 (`order_line`) + ORM SQLAlchemy 2.x async
- ✅ Pydantic v2 schemas + FastAPI routers (`/products`, `/orders`, `/orders/{id}/lines/{lineId}`)
- ✅ Feature-sliced `src/mirador_service/{order,product}/` + import-linter contracts (ADR-0007)
- ✅ 12 product router tests + workaround SQLAlchemy 2.0.36 + Python 3.14 union bug

### Reste à compléter (post-foundation)

- ☐ **ADR data model** : documenter Order ↔ Product ↔ OrderLine + justifier
  OrderLine comme entité (snapshot prix, statut individuel, refund par ligne).
- ☐ **Coverage ≥ 90 %** sur `src/mirador_service/{order,product}/` —
  cf. ADR-0014. Si manque, combler avec property tests Hypothesis.
- ☐ **Property-based tests Hypothesis** (cf. ADR-0011 §"Where to use") :
  `total_amount == sum(l.quantity * l.unit_price_at_order for l in lines)`,
  `stock_quantity ≥ 0`, immutabilité `unit_price_at_order`,
  transitions `Order.status` valides.
- ☐ **pytest-asyncio integration tests** (`tests/integration/`) :
  full HTTP roundtrip via `httpx.AsyncClient` + Postgres testcontainer ;
  POST /orders avec 2 OrderLines + assert total recalculé ; DELETE /orders/{id}
  cascade sur OrderLines.
- ☐ **`stability-check.sh` section 3** doit afficher 🟢 sur le nouveau code.
- ☐ **`bin/dev/api-smoke.sh`** : ajouter POST /orders avec 2 OrderLines,
  GET, DELETE, vérifier total.

### Cross-repo coordination (ADR-0001 polyrepo)

OpenAPI contract aligné avec [Java](https://gitlab.com/mirador1/mirador-service-java)
— UI ([mirador-ui](https://gitlab.com/mirador1/mirador-ui)) bascule transparemment
entre les 2 backends.
