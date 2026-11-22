"""Tests for the ingest use case with a fake client and real Parquet storage."""

import math
from collections.abc import Sequence
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from fxcast.ingest.series import BUY, SELL
from fxcast.ingest.service import (
    SERIES_START,
    NoDataError,
    resolve_window,
    run_ingest,
)
from fxcast.storage import ParquetStorage

TODAY = date(2026, 11, 23)  # Monday


class FakeClient:
    """Returns rows from an in-memory 'API' for the requested window; records calls."""

    def __init__(self, rows: dict[str, tuple[float, float]]) -> None:
        index = pd.DatetimeIndex(pd.to_datetime(list(rows)), name="date")
        self.data = pd.DataFrame(list(rows.values()), index=index, columns=[BUY.code, SELL.code])
        self.calls: list[tuple[list[str], date, date]] = []

    def fetch(self, codes: Sequence[str], start: date, end: date) -> pd.DataFrame:
        self.calls.append((list(codes), start, end))
        mask = (self.data.index >= pd.Timestamp(start)) & (self.data.index <= pd.Timestamp(end))
        return self.data.loc[mask, list(codes)]


API = {
    "2026-11-17": (3.410, 3.412),
    "2026-11-18": (3.430, 3.432),
    "2026-11-19": (3.439, 3.441),
}


@pytest.fixture
def storage(tmp_path: Path) -> ParquetStorage:
    return ParquetStorage(tmp_path / "rates.parquet")


# --- resolve_window (pure) -----------------------------------------------------


def test_incremental_window_refetches_ten_business_days() -> None:
    start, end = resolve_window(last_stored=date(2026, 11, 19), today=TODAY)
    assert start == date(2026, 11, 5)  # Thu 19 Nov - 10 business days
    assert end == TODAY


def test_backfill_window_starts_at_series_start() -> None:
    assert resolve_window(last_stored=None, today=TODAY, backfill=True) == (SERIES_START, TODAY)


def test_explicit_range_is_respected() -> None:
    window = resolve_window(
        last_stored=None, today=TODAY, start=date(2020, 1, 1), end=date(2020, 12, 31)
    )
    assert window == (date(2020, 1, 1), date(2020, 12, 31))


def test_incremental_without_data_asks_for_backfill() -> None:
    with pytest.raises(NoDataError, match="--backfill"):
        resolve_window(last_stored=None, today=TODAY)


def test_backfill_and_start_are_mutually_exclusive() -> None:
    with pytest.raises(ValueError, match="either --backfill or --start"):
        resolve_window(last_stored=None, today=TODAY, backfill=True, start=date(2020, 1, 1))


def test_start_after_end_raises() -> None:
    with pytest.raises(ValueError, match="after end"):
        resolve_window(last_stored=None, today=TODAY, start=date(2026, 12, 1))


# --- run_ingest ----------------------------------------------------------------


def test_backfill_stores_semantic_columns(storage: ParquetStorage) -> None:
    client = FakeClient(API)

    report = run_ingest(client=client, storage=storage, today=TODAY, backfill=True)

    assert client.calls == [([BUY.code, SELL.code], SERIES_START, TODAY)]
    assert report.result.inserted == 3
    assert list(storage.read().columns) == ["buy", "sell"]


def test_second_run_is_a_noop(storage: ParquetStorage) -> None:
    client = FakeClient(API)
    run_ingest(client=client, storage=storage, today=TODAY, backfill=True)

    report = run_ingest(client=client, storage=storage, today=TODAY)

    assert not report.result.changed
    assert client.calls[-1][1] == date(2026, 11, 5)  # incremental window


def test_new_day_and_revision_are_picked_up(storage: ParquetStorage) -> None:
    run_ingest(client=FakeClient(API), storage=storage, today=TODAY, backfill=True)
    tomorrow_api = {**API, "2026-11-19": (3.439, 3.445), "2026-11-20": (3.45, math.nan)}

    report = run_ingest(client=FakeClient(tomorrow_api), storage=storage, today=TODAY)

    assert (report.result.inserted, report.result.updated) == (1, 1)
    assert storage.read().loc["2026-11-19", "sell"] == 3.445
