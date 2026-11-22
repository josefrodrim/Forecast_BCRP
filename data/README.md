# data

Small, versioned artifacts (Parquet/JSON) produced by the daily pipeline and read by the web.
Committed by the daily workflow; each commit triggers a web redeploy.

Not versioned: `data/raw/`, `data/tmp/` (see `.gitignore`).
