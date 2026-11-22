# orchestration/airflow

Alternative orchestrator for local runs: `docker-compose` + DAG `fx_daily`.
The DAG calls the **same** `fxcast` CLI used by GitHub Actions — the pipeline is orchestrator-agnostic.
