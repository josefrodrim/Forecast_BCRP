# 0001. Monorepo with a uv-managed Python package in src layout

- **Status:** accepted
- **Date:** 2026-11-22

## Context

The project has several parts that evolve together: a Python pipeline, a static
Next.js site that reads the pipeline's exported artifacts, CI/CD workflows, and
alternative orchestration/lakehouse setups. A change to the exported data format
touches both the pipeline and the web. Environments must be identical on a laptop,
in GitHub Actions and in Docker. Only OSI-licensed tooling is allowed.

## Options considered

1. **Polyrepo** (pipeline, web, infra in separate repos) — independent versioning,
   but cross-cutting changes need coordinated PRs, and the daily data commit could
   not trigger the web deploy directly.
2. **Monorepo** — one PR for cross-cutting changes; daily `/data` commit triggers
   the web redeploy. Cost: CI must filter by `paths:`.
3. **Package manager:** pip + requirements.txt (no real lock of transitive deps),
   Poetry (slower, own non-standard sections historically), **uv** (PEP 621/735
   native, fast, universal `uv.lock`, manages Python versions itself).
4. **Layout:** flat (`fxcast/` at root) vs **src layout** (`src/fxcast/`).

## Decision

- **Monorepo.** Python package lives in `pipeline/` with its own `pyproject.toml`
  (not at the repo root), so the Docker build context is just `pipeline/` and
  the web never mixes with Python tooling.
- **uv** (Apache-2.0 / MIT) for dependencies, lockfile and Python version
  (`.python-version` = 3.12; `requires-python >= 3.11` for the CI matrix).
  Build backend: `uv_build`.
- **src layout**, so tests always import the *installed* package; packaging bugs
  surface locally instead of in Docker.
- Tool versions (ruff, mypy, pre-commit) live only in `uv.lock`; pre-commit uses
  `repo: local` hooks via `uv run` to avoid a second source of versions.

## Consequences

- One `uv sync` reproduces the environment exactly; CI will use `uv sync --locked`.
- Commands must target the subproject (`uv run --project pipeline ...` from the
  root, or `cd pipeline`). mypy specifically needs `--directory pipeline` because
  it reads its config from the current working directory.
- CI workflows need path filters to avoid running Python jobs on web-only changes.
