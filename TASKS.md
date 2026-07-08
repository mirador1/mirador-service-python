# TASKS — iris-service-python

Open work only. Per `~/.claude/CLAUDE.md` rules : Python-only items
here ; done items removed (use `git tag -l` for history).

---

## 🚫 Blocked upstream

- **Docker image alpine** : 412 MB → ~280 MB possible. Re-checked
  2026-07-08 : the three original blockers are RESOLVED (PyPI now has
  musllinux wheels for `pydantic_core` 2.47, `bcrypt` 5.0,
  `cryptography` 49.0, aarch64 + x86_64). NEW blocker : `onnxruntime`
  (runtime dep since Phase C churn serving) ships no musllinux wheel
  as of 1.27.0 and Microsoft has no musl CI — unlikely soon. Options
  when revisiting : (a) wait for onnxruntime musl wheels, (b) split
  serving into an optional extra so the base image goes alpine and
  an ML variant stays bookworm — only worth it if the 130 MB matter.
