"""Command-line interface: the single entry point every orchestrator calls."""

from typing import Annotated

import typer

from fxcast import __version__

app = typer.Typer(
    help="PEN/USD Forecast Arena pipeline.",
    no_args_is_help=True,
)


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
) -> None:
    """PEN/USD Forecast Arena pipeline."""
