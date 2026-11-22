# 0003. Parquet file storage with idempotent upsert behind a Protocol

- **Status:** accepted
- **Date:** 2026-11-22

## Context

v1 must cost nothing to run: no database server. The data is small (~7,800 daily rows,
two series, ~107 KB) and must be versioned in git, because the static web reads it and
the daily workflow commits it. Running the pipeline twice on the same day must not
duplicate rows or produce a diff. Later phases may move to Postgres or a lakehouse.

## Options considered

1. **CSV** — human-readable diffs, but no types (dates and floats round-trip as text),
   larger, and float formatting can change between writers.
2. **Parquet (pyarrow)** — typed columnar format, compressed, read natively by pandas,
   DuckDB, Spark and JS. Binary: git cannot diff it.
3. **SQLite** — real upserts, but one more moving part and still a binary file in git.
4. **Append-only writes** vs. **upsert by date**.

## Decision

- One Parquet file, `data/rates.parquet`, columns `date` (Arrow `date32`), `buy`, `sell`
  (float64, full precision); semantic names instead of BCRP codes (codes only in
  `ingest/series.py`).
- `Storage` is a `typing.Protocol` with `read()` and `upsert(frame) -> UpsertResult`;
  `ParquetStorage` implements it structurally. A Postgres backend only needs those two
  methods.
- Upsert by date, **incoming values win** (BCRP is the source of truth), NaN == NaN counts
  as unchanged. `UpsertResult` reports inserted / updated / unchanged.
- **No-op skip:** when nothing changed the file is not rewritten, so a run without new
  data produces no git diff and no commit.
- **Atomic write:** temp file in the same directory + `os.replace`.
- Input frames are validated (DatetimeIndex, tz-naive, unique, no time component,
  same columns as stored) before anything is written.

## Consequences

- Idempotent by construction; safe to retry or re-run from any orchestrator.
- `git diff` shows "Binary file"; inspecting changes needs pandas/DuckDB. Acceptable for
  this size; the commit message carries the upsert summary.
- Whole-file rewrite on every change: fine at ~100 KB, not at GBs (lakehouse phase).
- pyarrow ships no type information: mypy override limited to `pyarrow.*`.
