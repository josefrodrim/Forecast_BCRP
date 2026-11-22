"""Storage interface and the shared upsert/merge logic."""

from dataclasses import dataclass
from typing import Protocol

import pandas as pd

INDEX_NAME = "date"


@dataclass(frozen=True)
class UpsertResult:
    inserted: int  # dates that did not exist before
    updated: int  # existing dates whose values changed (BCRP revisions, late data)
    unchanged: int  # existing dates with identical values

    @property
    def changed(self) -> bool:
        """False means a clean no-op: nothing was (or needs to be) written."""
        return self.inserted > 0 or self.updated > 0


class Storage(Protocol):
    """Anything that can read and upsert a daily time series frame.

    A ``Protocol`` is structural typing: any class with these methods is a
    ``Storage`` for mypy, no inheritance required. Parquet today; a Postgres
    implementation later only needs the same two methods.
    """

    def read(self) -> pd.DataFrame: ...

    def upsert(self, frame: pd.DataFrame) -> UpsertResult: ...


def validate_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Check the canonical shape and return a normalized copy.

    Canonical shape: unique, sorted ``DatetimeIndex`` named ``date`` at
    second resolution with no time component; float64 columns.
    """
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise ValueError(f"Index must be a DatetimeIndex, got {type(frame.index).__name__}")
    if frame.index.tz is not None:
        raise ValueError("Index must be tz-naive (daily dates, no time zone)")
    if frame.index.has_duplicates:
        raise ValueError("Index has duplicate dates")
    if (frame.index != frame.index.normalize()).any():
        raise ValueError("Index must contain dates only (no time component)")

    out = frame.astype("float64").sort_index()
    # Re-wrap: after astype/sort mypy only knows a generic Index. Second
    # resolution matches what the parser produces.
    out.index = pd.DatetimeIndex(out.index, name=INDEX_NAME).as_unit("s")
    return out


def merge_upsert(
    existing: pd.DataFrame, incoming: pd.DataFrame
) -> tuple[pd.DataFrame, UpsertResult]:
    """Merge ``incoming`` into ``existing``; incoming values win on shared dates.

    "Incoming wins" because the BCRP is the source of truth: re-fetched dates
    may carry revisions or values published late. NaN == NaN counts as
    unchanged (a holiday that is still a holiday is not an update).
    """
    incoming = validate_frame(incoming)
    if existing.empty:
        return incoming, UpsertResult(inserted=len(incoming), updated=0, unchanged=0)

    existing = validate_frame(existing)
    if list(existing.columns) != list(incoming.columns):
        raise ValueError(
            f"Schema mismatch: stored columns {list(existing.columns)}, "
            f"incoming {list(incoming.columns)}"
        )

    shared = incoming.index.intersection(existing.index)
    old, new = existing.loc[shared], incoming.loc[shared]
    same = (old == new) | (old.isna() & new.isna())
    n_unchanged = int(same.all(axis=1).sum())

    merged = pd.concat([existing.drop(index=shared), incoming]).sort_index()
    result = UpsertResult(
        inserted=len(incoming) - len(shared),
        updated=len(shared) - n_unchanged,
        unchanged=n_unchanged,
    )
    return merged, result
