"""Ingestion use case: decide the date window, fetch, rename, upsert.

Orchestrates the pieces (client, series, storage) without knowing about the
CLI, so it is testable with fakes and reusable from any orchestrator.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol
from zoneinfo import ZoneInfo

import pandas as pd

from fxcast.ingest.series import DEFAULT_SERIES, Series, codes, to_semantic_columns
from fxcast.storage import Storage, UpsertResult

# First calendar day requested on backfill; the first published value is 02.Jan.97.
SERIES_START = date(1997, 1, 1)
# Business days re-fetched before the last stored date: catches late
# publication and BCRP revisions. Re-fetching is cheap (one request).
REFETCH_BUSINESS_DAYS = 10
# BCRP dates are Lima calendar dates. GitHub runners use UTC: between 19:00
# and 24:00 Lima time, UTC is already "tomorrow".
LIMA = ZoneInfo("America/Lima")


class NoDataError(Exception):
    """Incremental ingest requested but nothing is stored yet."""


class SeriesClient(Protocol):
    def fetch(self, codes: Sequence[str], start: date, end: date) -> pd.DataFrame: ...


@dataclass(frozen=True)
class IngestReport:
    start: date
    end: date
    fetched_rows: int
    result: UpsertResult


def today_lima() -> date:
    return datetime.now(LIMA).date()


def resolve_window(
    *,
    last_stored: date | None,
    today: date,
    backfill: bool = False,
    start: date | None = None,
    end: date | None = None,
) -> tuple[date, date]:
    """Pick ``[start, end]`` for a run.

    - ``backfill``: from ``SERIES_START`` (incompatible with ``start``).
    - explicit ``start``: as given.
    - incremental: ``REFETCH_BUSINESS_DAYS`` before the last stored date.
    ``end`` defaults to today (Lima).
    """
    if backfill and start is not None:
        raise ValueError("Use either --backfill or --start, not both")

    window_end = end if end is not None else today
    if backfill:
        window_start = SERIES_START
    elif start is not None:
        window_start = start
    elif last_stored is None:
        raise NoDataError("No data stored yet: run 'fxcast ingest --backfill' first")
    else:
        offset = pd.offsets.BDay(REFETCH_BUSINESS_DAYS)
        window_start = (pd.Timestamp(last_stored) - offset).date()

    if window_start > window_end:
        raise ValueError(f"start ({window_start}) is after end ({window_end})")
    return window_start, window_end


def run_ingest(
    *,
    client: SeriesClient,
    storage: Storage,
    today: date,
    backfill: bool = False,
    start: date | None = None,
    end: date | None = None,
    series: Sequence[Series] = DEFAULT_SERIES,
) -> IngestReport:
    stored = storage.read()
    last_stored = None if stored.empty else stored.index.max().date()

    window_start, window_end = resolve_window(
        last_stored=last_stored, today=today, backfill=backfill, start=start, end=end
    )
    raw = client.fetch(codes(series), window_start, window_end)
    frame = to_semantic_columns(raw, series)
    result = storage.upsert(frame)
    return IngestReport(window_start, window_end, len(frame), result)
