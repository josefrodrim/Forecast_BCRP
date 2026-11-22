"""Command-line interface: the single entry point every orchestrator calls.

Conventions (for machines as much as humans):
- stdout: the result summary. stderr: logs, warnings and errors.
- Exit codes: 0 = success (including a no-op), 1 = pipeline error,
  2 = usage error (bad flags; produced by Typer/Click).
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer

from fxcast import __version__
from fxcast.ingest.client import BCRPClient, BCRPRequestError, BCRPUnavailableError
from fxcast.ingest.parse import BCRPParseError
from fxcast.ingest.service import NoDataError, run_ingest, today_lima
from fxcast.storage import ParquetStorage

app = typer.Typer(
    help="PEN/USD Forecast Arena pipeline.",
    no_args_is_help=True,
)

RATES_FILE = "rates.parquet"

# Errors we expect and can explain in one line; anything else is a bug and
# keeps its full traceback.
_KNOWN_ERRORS = (
    BCRPParseError,
    BCRPRequestError,
    BCRPUnavailableError,
    NoDataError,
    ValueError,
)

DataDir = Annotated[
    Path,
    typer.Option(
        envvar="FXCAST_DATA_DIR",
        help="Directory with the versioned data artifacts.",
        file_okay=False,
    ),
]
DateOption = Annotated[datetime | None, typer.Option(formats=["%Y-%m-%d"])]


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"fxcast {__version__}")
        raise typer.Exit


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            callback=_version_callback,
            # Eager: evaluated before anything else, so `--version` works
            # even when no subcommand is given.
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Log INFO to stderr.")] = False,
) -> None:
    """PEN/USD Forecast Arena pipeline."""
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


@app.command()
def ingest(
    data_dir: DataDir = Path("data"),
    backfill: Annotated[
        bool, typer.Option("--backfill", help="Fetch the full history since 1997.")
    ] = False,
    start: DateOption = None,
    end: DateOption = None,
) -> None:
    """Fetch BCRP exchange rates and upsert them into DATA_DIR/rates.parquet.

    Default (incremental): re-fetch the last 10 business days and upsert.
    Running it twice is safe: the second run is a no-op.
    """
    storage = ParquetStorage(data_dir / RATES_FILE)
    try:
        with BCRPClient() as client:
            report = run_ingest(
                client=client,
                storage=storage,
                today=today_lima(),
                backfill=backfill,
                start=start.date() if start else None,
                end=end.date() if end else None,
            )
    except _KNOWN_ERRORS as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    r = report.result
    status = "updated" if r.changed else "no-op"
    typer.echo(
        f"{status}: inserted={r.inserted} updated={r.updated} unchanged={r.unchanged} "
        f"window={report.start}..{report.end} -> {storage.path}"
    )
