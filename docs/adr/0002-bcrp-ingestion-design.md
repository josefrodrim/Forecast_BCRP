# 0002. BCRP ingestion: pure parser, explicit failure taxonomy, re-fetch window

- **Status:** accepted
- **Date:** 2026-11-22

## Context

The only data source is the public BCRPData API. Probing it (`notebooks/01_api.ipynb`)
revealed behavior that is not documented and that a naive client would get wrong:

- JSON bodies are served as `Content-Type: text/html`.
- An invalid series code returns `200` + an Imperva (Incapsula) WAF HTML page; the same
  page was observed for a *valid* request right after a burst, so it can be transient.
- The API returns the full Mon-Fri grid of the requested range: holidays, dates before
  the series starts and not-yet-published dates all come as `"n.d."`.
- Dates use 2-digit years and `"Set"` for September even with `/ing` (English).
- No maximum range: 1997-today for two series is one ~0.5 s request.

## Options considered

1. **One function that fetches and parses** — simplest, but every test needs the network
   or heavy mocking.
2. **Pure parser + thin HTTP shell** ("functional core, imperative shell") — parser
   tested with recorded fixtures, client tested with `httpx.MockTransport`.
3. **Retry library (tenacity) vs. hand-written retry loop** — tenacity is mature, but the
   loop is ~30 lines and the learning goal is to understand it.
4. **Incremental strategy:** fetch only dates after the last stored one, vs. **re-fetch a
   window** and upsert.

## Decision

- Option 2. `parse.py` has no I/O; `client.py` only performs the GET and classifies failures.
- Failure taxonomy:
  - *Transient* (retried, exponential backoff with full jitter, honors `Retry-After`):
    timeouts, network errors, HTTP 429/5xx and **non-JSON bodies**.
  - *Permanent* (raised immediately): other 4xx and contract violations (`BCRPParseError`).
- Strict parsing: own month map (`Set`/`Sep`), century resolved inside the requested
  range, `"n.d."` → NaN and anything else non-numeric (including `nan`/`inf`) raises.
  Never `errors="coerce"`.
- Leading/trailing all-`n.d.` rows are dropped (not published / before series start);
  interior ones (holidays) are kept as NaN.
- Incremental ingest re-fetches **10 business days** before the last stored date and
  upserts; backfill is a single request from 1997-01-01. "Today" is computed in
  `America/Lima`, not UTC.
- Generic default User-Agent; no personal or project data sent to the external API.

## Consequences

- Late publications and BCRP revisions are picked up automatically; re-running is safe.
- A format change fails the pipeline loudly on the same day instead of silently
  writing NaNs.
- A persistent WAF block is indistinguishable from an invalid code; the error message
  says so. Risk to validate early in CI: GitHub-hosted runners (datacenter IPs) may be
  blocked more often than a home connection.
- Fixtures must be re-recorded deliberately (`scripts/record_fixtures.py`) if the API changes;
  live contract tests (`pytest -m integration`) detect that drift.
