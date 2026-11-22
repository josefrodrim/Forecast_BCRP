"""BCRP series used by the project: codes live here and only here.

Downstream layers (storage, models, web) use the semantic ``name`` columns
(``buy``, ``sell``); the BCRP codes never leak past ingestion.
"""

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Series:
    code: str  # BCRPData series code (validated against the API in notebooks/01_api)
    name: str  # semantic column name used everywhere downstream
    description: str


BUY = Series("PD04637PD", "buy", "Interbank exchange rate, buying (S/ per US$)")
SELL = Series("PD04638PD", "sell", "Interbank exchange rate, selling (S/ per US$)")

DEFAULT_SERIES: tuple[Series, ...] = (BUY, SELL)


def codes(series: Sequence[Series]) -> list[str]:
    return [s.code for s in series]


def to_semantic_columns(frame: pd.DataFrame, series: Sequence[Series]) -> pd.DataFrame:
    """Rename BCRP code columns to semantic names (``PD04638PD`` -> ``sell``)."""
    mapping = {s.code: s.name for s in series}
    missing = set(mapping) - set(frame.columns)
    if missing:
        raise ValueError(f"Frame lacks series columns: {sorted(missing)}")
    return frame.rename(columns=mapping)[[s.name for s in series]]
