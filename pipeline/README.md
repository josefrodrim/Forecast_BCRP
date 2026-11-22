# pipeline

Python package `fxcast` (src layout, managed with [uv](https://docs.astral.sh/uv/)).
All production logic lives here: ingest, validate, features, models, backtest, forecast, export.

Everything runs through a single CLI, so any orchestrator (GitHub Actions, Airflow, cron) calls the same code:

```bash
fxcast ingest | validate | backtest | forecast | export
```
