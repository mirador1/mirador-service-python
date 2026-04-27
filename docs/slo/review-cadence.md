# SLO Review Cadence

> **Source of truth** : the cross-language review cadence is defined
> in [`infra/shared/docs/slo/review-cadence.md`](../../infra/shared/docs/slo/review-cadence.md)
> ([repo source](https://gitlab.com/mirador1/mirador-service-shared/-/blob/main/docs/slo/review-cadence.md))
> — same monthly / quarterly / post-incident loop applies to both
> `mirador-service-python` and `mirador-service-java`. Both services
> share the same SLO targets per [ADR-0058](https://gitlab.com/mirador1/mirador-service-shared/-/blob/main/docs/adr/0058-slo-sla-with-sloth.md),
> so reviews can be combined.

This file exists as a thin pointer so that `docs/slo/sla.md` and the
runbooks (`docs/runbooks/slo-*.md`) can link to a Python-local URL
for the cadence section, and so a session that opens the Python repo
in isolation discovers the cadence path without first stumbling into
the shared submodule.

## Python-specific addenda (only what differs from the shared cadence)

- **Compliance % source** : query against `sloth_service="mirador-service-python"`
  on the [SLO Overview dashboard](../../infra/shared/infra/observability/grafana/dashboards-lgtm/slo-overview.json).
- **Top burn contributors** : use [SLO Breakdown by Endpoint](../../infra/observability/grafana-dashboards/slo-breakdown-by-endpoint.json)
  with the dashboard variable filtered to Python's `path_template` label
  (Java's equivalent uses Micrometer's `uri` label).
- **Tail-latency analysis** : use [Latency Heatmap](../../infra/observability/grafana-dashboards/latency-heatmap.json)
  to see if breaches come from a small slow tail or a uniform shift.
- **User-satisfaction proxy** : use [Apdex](../../infra/observability/grafana-dashboards/apdex.json)
  to communicate health to non-SRE stakeholders in 1 number.

## See also

- [Shared review-cadence.md](../../infra/shared/docs/slo/review-cadence.md) —
  the canonical document.
- [Python SLA promise](sla.md).
- [Python SLO definitions](slo.yaml).
- [Chaos-driven SLO demo](chaos-demo.md) — for hands-on exploration of how the
  cadence questions get answered.
