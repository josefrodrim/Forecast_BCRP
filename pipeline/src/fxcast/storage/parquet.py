"""Parquet-backed storage: a single file, written atomically."""

import os
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from fxcast.storage.base import INDEX_NAME, UpsertResult, merge_upsert, validate_frame


class ParquetStorage:
    """Store a daily frame as one Parquet file.

    - ``date`` is written as Arrow ``date32`` (a calendar date, no time/zone),
      so any reader (DuckDB, Spark, JS) sees a plain date.
    - Writes are atomic: write a temp file in the same directory, then
      ``os.replace`` it over the target. A crash mid-write leaves the old
      file intact instead of a truncated, corrupt one.
    - A no-op upsert does not touch the file, so a daily run with no new data
      produces no git diff (and no pointless commit).
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def read(self) -> pd.DataFrame:
        if not self.path.exists():
            return pd.DataFrame(index=pd.DatetimeIndex([], name=INDEX_NAME, dtype="datetime64[s]"))
        frame = pq.read_table(self.path).to_pandas()
        frame[INDEX_NAME] = pd.to_datetime(frame[INDEX_NAME])
        return validate_frame(frame.set_index(INDEX_NAME))

    def upsert(self, frame: pd.DataFrame) -> UpsertResult:
        merged, result = merge_upsert(self.read(), frame)
        if result.changed:
            self._write_atomic(merged)
        return result

    def _write_atomic(self, frame: pd.DataFrame) -> None:
        table = pa.Table.from_pandas(frame.reset_index(), preserve_index=False)
        date_idx = table.schema.get_field_index(INDEX_NAME)
        table = table.set_column(date_idx, INDEX_NAME, table.column(INDEX_NAME).cast(pa.date32()))

        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(f".{self.path.name}.tmp")  # same dir -> same filesystem
        try:
            pq.write_table(table, tmp, compression="zstd")
            os.replace(tmp, self.path)  # atomic rename on POSIX and Windows
        finally:
            tmp.unlink(missing_ok=True)
