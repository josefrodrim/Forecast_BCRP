"""Tests for the CLI: wiring, output streams and exit codes."""

from collections.abc import Sequence
from datetime import date
from pathlib import Path
from types import TracebackType
from typing import Self

import pandas as pd
import pytest
from typer.testing import CliRunner

from fxcast import __version__, cli
from fxcast.ingest.client import BCRPUnavailableError

runner = CliRunner()


class StubClient:
    """Stands in for BCRPClient; behavior set per test via class attributes."""

    frame: pd.DataFrame | None = None
    error: Exception | None = None

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    def fetch(self, codes: Sequence[str], start: date, end: date) -> pd.DataFrame:
        if self.error is not None:
            raise self.error
        assert self.frame is not None
        return self.frame


@pytest.fixture(autouse=True)
def stub_io(monkeypatch: pytest.MonkeyPatch) -> None:
    index = pd.DatetimeIndex(pd.to_datetime(["2026-11-18", "2026-11-19"]), name="date")
    StubClient.frame = pd.DataFrame(
        {"PD04637PD": [3.43, 3.439], "PD04638PD": [3.432, 3.441]}, index=index
    )
    StubClient.error = None
    monkeypatch.setattr(cli, "BCRPClient", StubClient)
    monkeypatch.setattr(cli, "today_lima", lambda: date(2026, 11, 23))


def test_version_flag_prints_version() -> None:
    result = runner.invoke(cli.app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == f"fxcast {__version__}"


def test_backfill_then_noop(tmp_path: Path) -> None:
    args = ["ingest", "--data-dir", str(tmp_path)]

    first = runner.invoke(cli.app, [*args, "--backfill"])
    second = runner.invoke(cli.app, args)

    assert first.exit_code == 0, first.output
    assert first.stdout.startswith("updated: inserted=2")
    assert second.exit_code == 0
    assert second.stdout.startswith("no-op: inserted=0 updated=0 unchanged=2")
    assert (tmp_path / "rates.parquet").exists()


def test_incremental_without_data_fails_with_hint(tmp_path: Path) -> None:
    result = runner.invoke(cli.app, ["ingest", "--data-dir", str(tmp_path)])

    assert result.exit_code == 1
    assert "fxcast ingest --backfill" in result.stderr
    assert result.stdout == ""  # errors go to stderr only


def test_api_outage_is_a_clean_error(tmp_path: Path) -> None:
    StubClient.error = BCRPUnavailableError("BCRP API unavailable after 5 attempts")

    result = runner.invoke(cli.app, ["ingest", "--data-dir", str(tmp_path), "--backfill"])

    assert result.exit_code == 1
    assert result.stderr.startswith("error: BCRP API unavailable")
    assert "Traceback" not in result.output


def test_data_dir_from_environment(tmp_path: Path) -> None:
    result = runner.invoke(
        cli.app, ["ingest", "--backfill"], env={"FXCAST_DATA_DIR": str(tmp_path)}
    )

    assert result.exit_code == 0
    assert (tmp_path / "rates.parquet").exists()


def test_bad_date_is_a_usage_error(tmp_path: Path) -> None:
    result = runner.invoke(
        cli.app, ["ingest", "--data-dir", str(tmp_path), "--start", "22/11/2026"]
    )

    assert result.exit_code == 2
