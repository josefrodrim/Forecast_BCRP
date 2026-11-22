"""Persistence behind a small interface, so the backend can change (Parquet -> Postgres)."""

from fxcast.storage.base import Storage, UpsertResult
from fxcast.storage.parquet import ParquetStorage

__all__ = ["ParquetStorage", "Storage", "UpsertResult"]
