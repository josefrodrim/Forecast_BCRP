"""Tests for the series registry."""

import pandas as pd
import pytest

from fxcast.ingest.series import BUY, DEFAULT_SERIES, SELL, codes, to_semantic_columns


def test_codes_keep_order() -> None:
    assert codes(DEFAULT_SERIES) == ["PD04637PD", "PD04638PD"]


def test_to_semantic_columns_renames_and_orders() -> None:
    raw = pd.DataFrame({SELL.code: [3.41], BUY.code: [3.40]})
    out = to_semantic_columns(raw, DEFAULT_SERIES)
    assert list(out.columns) == ["buy", "sell"]
    assert out.loc[0, "sell"] == 3.41


def test_to_semantic_columns_missing_code_raises() -> None:
    with pytest.raises(ValueError, match="PD04637PD"):
        to_semantic_columns(pd.DataFrame({SELL.code: [3.41]}), DEFAULT_SERIES)
