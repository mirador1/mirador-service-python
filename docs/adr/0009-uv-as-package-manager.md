# ADR-0009 : `uv` as package manager (replaces pip + setuptools + pyenv)

**Status** : Accepted
**Date** : 2026-04-25
**Supersedes** : implicit "pip + setuptools + pyenv + virtualenv" baseline.

## Context

Python's tooling ecosystem evolved by accretion : `pip` (installer),
`setuptools` (build backend), `virtualenv` / `venv` (isolation), `pyenv`
(interpreter management), `pip-tools` / `poetry` / `pdm` / `hatch` /
`rye` (dependency resolvers + lockfiles). Every team picks 3-4 of these
and the combination drifts across CI, dev laptops, and Docker images.

Pain points :
- **Slow** : `pip install -r requirements.txt` on a clean cache = 30-60s.
- **Lockfile is BYO** : pip-tools, poetry, pdm each ship their own format.
- **Cross-platform resolution** : pip resolves for ONE platform at a time
  (macOS arm64 dev → fails on linux/amd64 CI when wheels differ).
- **Python interpreter management** : `pyenv` is a separate tool, requires
  shell hooks, breaks on macOS Sonoma / Sequoia upgrades.

## Decision

Adopt **[uv](https://docs.astral.sh/uv/)** (Astral, Rust) as the SINGLE tool
covering all the above. `uv` replaces :

| Legacy tool(s) | uv equivalent |
|---|---|
| `pip install` | `uv sync` (fast resolver + content-addressed cache) |
| `pip-tools`, `poetry lock`, `pdm lock` | `uv lock` → `uv.lock` (cross-platform) |
| `virtualenv`, `python -m venv` | `uv venv` (auto-managed per project) |
| `pyenv`, `pyenv-virtualenv` | `uv python install 3.14` (downloads from python-build-standalone) |
| `pipx` | `uv tool install ruff` |
| `setuptools.build_meta` | `uv_build` (build backend, used in `pyproject.toml [build-system]`) |
| `pip-audit` (still used) | wraps it via `uv run pip-audit` |

CI image : `ghcr.io/astral-sh/uv:python3.14-bookworm-slim` ships uv +
Python preinstalled. Local dev : `brew install uv`.

## Consequences

**Pros** :
- **Speed** : `uv sync` ~5-10× faster than `pip install` on cold cache, ~50×
  faster on warm cache. Verified on this project : `pip install ...` 25s →
  `uv sync` 3s.
- **Single binary** : 35 MB Rust binary, no Python dependency for the
  installer itself (chicken-and-egg solved).
- **Lockfile cross-platform** : `uv.lock` resolves for ALL declared platforms
  (macOS arm64 + linux/amd64 + linux/aarch64 + win) in one pass. CI on linux
  uses the same lock as macOS dev.
- **Reproducibility** : `uv sync --frozen` installs EXACTLY the locked
  versions ; CI rejects any drift.
- **PEP-compliant** : `uv_build` respects PEP 517/518/621. Drop-in,
  no lock-in (any project can switch back to pip if uv ever fades).
- **Python interpreter built-in** : `uv python install 3.14` downloads from
  python-build-standalone (Indygreg's distribution). No `pyenv` needed.
- **CLI tool runner** : `uv run ruff check` works without installing ruff
  globally — uv handles the implicit venv.

**Cons** :
- **Newness** : uv 0.11 (Apr 2026) is still pre-1.0. Breaking changes possible
  in major bumps. Mitigation : pin `uv_build>=0.11.2,<0.12.0` in `[build-system]`.
- **Lock-in to Astral** : if Astral disappears, the `uv.lock` format is
  non-standard. Mitigation : `uv export --format requirements-txt` produces
  a pip-compatible requirements file ; emergency exit always available.
- **CI image** : Astral-published image pulls from ghcr.io. If unavailable,
  fall back to building uv from source (~10s on Rust-cached image).

**Alternatives considered** :

| Tool | Why not |
|---|---|
| **Poetry** | Slower, lockfile non-cross-platform, custom `[tool.poetry]` format (uv stays on PEP 621 standard) |
| **PDM** | Performances proches uv mais écosystème CI/wheels moins large |
| **Hatch** | Excellent for build, weak resolver |
| **Rye** | Astral merged it into uv in 2024 — uv IS the rye successor |
| **pip-tools** | Just lockfile, doesn't solve the venv/interpreter/build-backend problems |

## Validation

- `uv --version` → 0.11.2 (Homebrew) on macOS.
- `uv sync --frozen` in CI : 5 jobs run with cached wheels, total install
  time < 8s vs ~40s on the previous pip-tools setup.
- `pyproject.toml [build-system]` uses `uv_build` ; `uv build` produces
  wheel + sdist passing PyPI's `twine check`.
- Lockfile committed (see ADR-0007 §9 + the dev session 2026-04-25 fixing
  the gitignored uv.lock that was breaking `--frozen` in CI).

## See also

- ADR-0001 : Python stack choice
- ADR-0007 : Industrial Python practices
- [uv documentation](https://docs.astral.sh/uv/)
- [python-build-standalone](https://github.com/indygreg/python-build-standalone)
