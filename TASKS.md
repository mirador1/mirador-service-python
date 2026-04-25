# TASKS — mirador-service-python

Open work only. Per `~/.claude/CLAUDE.md` rules : Python-only items
here ; done items removed (use `git tag -l` for history).

---

## 🤔 À considérer (lower priority)

- 🟢 **`/customers/{id}/bio`** : Ollama LLM call + tenacity retry, mirror
  of Java side. Defer until docker-compose includes ollama service.

- 🟢 **README.fr.md** — French localised README (mirror UI repo pattern).

- 🟢 **Replace `python-jose`** with `pyjwt` — python-jose semi-abandoned
  (last release 2022-12). pyjwt actively maintained ; migration
  straightforward. ADR + PR.

- 🟢 **Replace `passlib`** with `argon2-cffi` or `bcrypt ≥ 4.x` — passlib
  semi-abandoned ; bcrypt 5.x compat issue forced 3.2.2 pin. argon2-cffi
  is the modern recommendation.

- 🟢 **Docker image size optimisation** : currently 412 MB. Tried alpine
  (would save ~130 MB) but pydantic_core's Rust binary is glibc-only.
  Revisit when uv ships musl wheels for all Rust-extension deps
  (pydantic_core, cryptography, bcrypt).

- 🟢 **GitHub mirror** : Python repo not yet pushed to a github mirror.
  Java + UI both have one. Set up `git remote add github ...` + auto-push
  cron under `bin/launchd/`.
