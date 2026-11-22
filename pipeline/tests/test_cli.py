"""Smoke tests for the CLI entry point."""

from typer.testing import CliRunner

from fxcast import __version__
from fxcast.cli import app

runner = CliRunner()


def test_version_flag_prints_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == f"fxcast {__version__}"
