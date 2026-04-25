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
