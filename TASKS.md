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

- 🚫 **Flip integration-tests CI job to required** (`allow_failure:
  false`) : currently 0 / 23 consecutive green runs on main (audited
  2026-04-27). Both root causes need to be fixed BEFORE flipping :
  (1) testcontainers-ryuk 409 conflict on the local runner — leftover
  ryuk container from a prior run blocks the new test session ;
  needs `docker rm $(docker ps -aq --filter name=testcontainers-ryuk)`
  added to the runner's pre-job hook OR `TESTCONTAINERS_RYUK_DISABLED=true`
  on the job ; (2) `test_kafka_*` integration tests connect to Kafka
  but the job's `services:` block only declares `postgres` —
  add Kafka via testcontainers-kafka (already imported) OR via
  GitLab `services:` with the right alias.

- 🚫 **Flip sonarcloud to required** (`allow_failure: false` →
  remove the line) : `sonarcloud` job is rule-skipped on every main
  pipeline because `SONAR_TOKEN` is not set at the project / group
  level. 0 / 23 actual runs on main (audited 2026-04-27). To unblock :
  set `SONAR_TOKEN` (group var, masked, protected) ; observe 5
  consecutive green runs ; THEN flip. Keep the dated TODO 2026-05-25
  in quality.yml as a re-check trigger.

- 🟢 **Migrate Java's `jvm.config` Comments rule to Python's
  `pytest.ini_options`** : adopt the same dated-TODO comment pattern
  for `allow_failure` shields once we have any.

## 📊 SLO/SLA backlog (post Quick wins ADR-0058)

Quick wins SHIPPED 2026-04-25 : 3 SLOs as code (Sloth) + multi-burn-rate
alerting + Grafana SLO dashboard + ADR-0058 + sla.md.

Iteration-2 SHIPPED 2026-04-27 in [stable-py-v0.6.8](https://gitlab.com/mirador1/mirador-service-python/-/tags/stable-py-v0.6.8) :
- ✅ SLO breakdown by endpoint dashboard (`infra/observability/grafana-dashboards/slo-breakdown-by-endpoint.json`) — top 10 endpoints by 5xx rate / p99 latency / request rate / budget burn share.
- ✅ Latency heatmap dashboard — service-wide + per-endpoint via `path_template` variable.
- ✅ Apdex dashboard — gauge + breakdown + over-time view.
- ✅ Chaos-driven SLO demo wiring — 3 chaos annotations on the breakdown dashboard + `docs/slo/chaos-demo.md` step-by-step guide.
- ✅ 3 runbooks (`slo-availability.md`, `slo-latency.md`, `slo-enrichment.md`) — already populated in stable-py-v0.6.6, links no longer 404.
- ✅ `docs/slo/review-cadence.md` thin pointer to the cross-language shared cadence doc.

## 🎨 README polish

Major sync wave **shipped 2026-04-27** :
- ✅ README.fr.md mastery block + 8-row matrix ([!41](https://gitlab.com/mirador1/mirador-service-python/-/merge_requests/41))
- ✅ mkdocs landing refresh ([!42](https://gitlab.com/mirador1/mirador-service-python/-/merge_requests/42))
- The English README already had the senior-architect matrix on main ; no separate "add it to Python" item left.

Remaining (low priority) :
- 🟢 **Mini-domain rename consideration** : `Customer*` classes still
  named after the old framing. Refactor 50+ files when there's a real
  recruiter signal that the term feels generic. Narrative in README
  is enough today.

## 🎯 Surface fonctionnelle — entités e-commerce

Foundation **shippée 2026-04-26** dans [stable-py-v0.6.4](https://gitlab.com/mirador1/mirador-service-python/-/tags/stable-py-v0.6.4) :
- ✅ Alembic 0002 (`product`), 0003 (`orders`), 0004 (`order_line`) + ORM SQLAlchemy 2.x async
- ✅ Pydantic v2 schemas + FastAPI routers (`/products`, `/orders`, `/orders/{id}/lines/{lineId}`)
- ✅ Feature-sliced `src/mirador_service/{order,product}/` + import-linter contracts (ADR-0007)
- ✅ 12 product router tests + workaround SQLAlchemy 2.0.36 + Python 3.14 union bug

### Reste à compléter (post-foundation)

Wave **shippée 2026-04-27** :
- ✅ ADR data model (shared ADR-0059)
- ✅ `bin/dev/api-smoke.sh` POST /orders + 2 lines + GET + DELETE + total assertion + new PUT /orders/{id}/status flow ([!44](https://gitlab.com/mirador1/mirador-service-python/-/merge_requests/44))
- ✅ Server-side product search ([!40](https://gitlab.com/mirador1/mirador-service-python/-/merge_requests/40))
- ✅ PUT /orders/{id}/status state-machine endpoint ([!43](https://gitlab.com/mirador1/mirador-service-python/-/merge_requests/43))
- ✅ GET /products/{id}/orders ([!45](https://gitlab.com/mirador1/mirador-service-python/-/merge_requests/45))

Remaining :
- ☐ **Property-based tests Hypothesis** (cf. ADR-0011 §"Where to use") :
  `total_amount == sum(l.quantity * l.unit_price_at_order for l in lines)`,
  `stock_quantity ≥ 0`, immutabilité `unit_price_at_order`,
  transitions `Order.status` valides. Scheduled for the
  [java-ecommerce-coverage-batch](file:///Users/benoitbesson/.claude/scheduled-tasks/java-ecommerce-coverage-batch/SKILL.md)
  agent (2026-05-04 ; covers Java + Python parallel).
- ☐ **pytest-asyncio integration tests** (`tests/integration/`) :
  full HTTP roundtrip via `httpx.AsyncClient` + Postgres testcontainer ;
  POST /orders avec 2 OrderLines + assert total recalculé ; DELETE /orders/{id}
  cascade sur OrderLines. Currently blocked by the testcontainers ryuk
  issue on the local runner (see "À considérer" above).
- ☐ **`stability-check.sh` section 3** doit afficher 🟢 sur le nouveau code.

### Cross-repo coordination (ADR-0001 polyrepo)

OpenAPI contract aligné avec [Java](https://gitlab.com/mirador1/mirador-service-java)
— UI ([mirador-ui](https://gitlab.com/mirador1/mirador-ui)) bascule transparemment
entre les 2 backends.
