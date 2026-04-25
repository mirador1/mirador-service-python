# TASKS — mirador-service-python

Open work only. Per `~/.claude/CLAUDE.md` rules : Python-only items
here ; done items removed (use `git tag -l` for history).

---

## 🤔 À considérer (lower priority)

- 🟢 **Docker image size optimisation** : currently 412 MB. Tried alpine
  (would save ~130 MB) but pydantic_core's Rust binary is glibc-only.
  Revisit when uv ships musl wheels for all Rust-extension deps
  (pydantic_core, cryptography, bcrypt).

- 🟢 **pytest-benchmark gate** (ADR-0007 §13 TODO) : add benchmarks for
  hot paths (JWT verify, password hash, repository search) + JSON
  output for CI delta tracking. Right-sized for portfolio demo : skip
  for now, revisit if a real perf regression lands.

- 🟢 **kafka_client integration coverage** : producer + consumer loops
  are at 43% (the rest needs a real broker). Run via `pytest -m
  integration` with testcontainers Kafka — already wired in
  `.gitlab-ci/test.yml :: integration-tests`. Local dev rarely runs
  this ; flip to required gate (`allow_failure: false`) after the
  integration job has 5 consecutive green runs.

- 🟢 **pip-audit / safety in CI** (ADR-0007 §9 TODO) : add a job that
  scans pyproject.toml for dependencies with known CVEs. Already have
  gitleaks (secrets) + renovate (updates) ; CVE scanning is the third
  leg.

- 🟢 **Replace dict-based Todo / OllamaResponse types with Pydantic
  models** : currently aliased as `dict[str, Any]` for simplicity.
  Migration is a single-line type change per call site. Defer until
  consumers actually need typed field access (currently they just
  return the dicts as-is to the wire).
