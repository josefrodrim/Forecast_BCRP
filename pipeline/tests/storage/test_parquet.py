"""Tests for the Parquet storage: round-trip, idempotent upsert, atomic writes."""

import math
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from fxcast.storage import ParquetStorage, Storage


def frame(rows: dict[str, tuple[float, float]]) -> pd.DataFrame:
    """Build a canonical frame: {"2026-07-24": (buy, sell), ...}."""
    return pd.DataFrame(
        list(rows.values()),
        index=pd.DatetimeIndex(pd.to_datetime(list(rows)), name="date"),
        columns=["buy", "sell"],
    )


BASE = frame(
    {
        "2026-07-24": (3.403, 3.406),
        "2026-07-27": (math.nan, math.nan),  # holiday
        "2026-07-30": (3.391, 3.393),
    }
)


@pytest.fixture
def store(tmp_path: Path) -> ParquetStorage:
    return ParquetStorage(tmp_path / "data" / "rates.parquet")


def test_satisfies_storage_protocol(store: ParquetStorage) -> None:
    storage: Storage = store  # mypy checks this structurally
    assert storage is store


def test_read_missing_file_returns_empty(store: ParquetStorage) -> None:
    assert store.read().empty


def test_first_upsert_inserts_and_round_trips(store: ParquetStorage) -> None:
    result = store.upsert(BASE)

    assert (result.inserted, result.updated, result.unchanged) == (3, 0, 0)
    stored = store.read()
    expected = BASE.set_axis(pd.DatetimeIndex(BASE.index, name="date").as_unit("s"))
    pd.testing.assert_frame_equal(stored, expected)
    assert stored.loc["2026-07-27"].isna().all()  # NaN preserved, row kept


def test_date_is_stored_as_calendar_date(store: ParquetStorage) -> None:
    store.upsert(BASE)
    assert pq.read_schema(store.path).field("date").type == pa.date32()


def test_second_identical_upsert_is_a_noop(store: ParquetStorage) -> None:
    store.upsert(BASE)
    bytes_before = store.path.read_bytes()
    mtime_before = store.path.stat().st_mtime_ns

    result = store.upsert(BASE)

    assert not result.changed
    assert result.unchanged == 3
    assert store.path.read_bytes() == bytes_before
    assert store.path.stat().st_mtime_ns == mtime_before  # file not even rewritten


def test_overlap_counts_inserts_updates_and_unchanged(store: ParquetStorage) -> None:
    store.upsert(BASE)
    incoming = frame(
        {
            "2026-07-27": (math.nan, math.nan),  # unchanged holiday (NaN == NaN)
            "2026-07-30": (3.391, 3.399),  # revised by the BCRP
            "2026-07-31": (3.396, 3.398),  # new date
        }
    )

    result = store.upsert(incoming)

    assert (result.inserted, result.updated, result.unchanged) == (1, 1, 1)
    stored = store.read()
    assert len(stored) == 4
    assert stored.loc["2026-07-30", "sell"] == 3.399  # incoming wins
    assert stored.loc["2026-07-24", "sell"] == 3.406  # outside the overlap: untouched


def test_unsorted_input_is_stored_sorted(store: ParquetStorage) -> None:
    store.upsert(BASE.iloc[::-1])
    assert store.read().index.is_monotonic_increasing


def test_schema_mismatch_raises(store: ParquetStorage) -> None:
    store.upsert(BASE)
    with pytest.raises(ValueError, match="Schema mismatch"):
        store.upsert(BASE.rename(columns={"sell": "venta"}))


@pytest.mark.parametrize(
    ("bad", "match"),
    [
        (BASE.reset_index(drop=True), "DatetimeIndex"),
        (pd.concat([BASE, BASE.iloc[:1]]), "duplicate"),
        (BASE.set_axis(BASE.index + pd.Timedelta(hours=10)), "dates only"),
        (BASE.tz_localize("America/Lima"), "tz-naive"),
    ],
    ids=["no-datetime-index", "duplicates", "time-component", "tz-aware"],
)
def test_invalid_frames_are_rejected(store: ParquetStorage, bad: pd.DataFrame, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        store.upsert(bad)


def test_failed_write_keeps_previous_file_intact(
    store: ParquetStorage, monkeypatch: pytest.MonkeyPatch
) -> None:
    store.upsert(BASE)
    good_bytes = store.path.read_bytes()

    def crash(*args: object, **kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(pq, "write_table", crash)
    with pytest.raises(OSError, match="disk full"):
        store.upsert(frame({"2026-08-03": (3.4, 3.41)}))

    assert store.path.read_bytes() == good_bytes  # old data survives the crash
    assert list(store.path.parent.iterdir()) == [store.path]  # no temp file left behind
