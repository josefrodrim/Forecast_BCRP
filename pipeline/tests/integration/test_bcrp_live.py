"""Live contract tests against the real BCRPData API.

Deselected by default (see addopts in pyproject.toml). Run on demand:

    uv run pytest -m integration

They answer one question: do the assumptions baked into our parser and
fixtures still hold for the real API today? If one fails, re-record the
fixtures (scripts/record_fixtures.py) and review the diff.
"""

from datetime import date

import pytest

from fxcast.ingest.client import BCRPClient, BCRPUnavailableError, RetryPolicy
from fxcast.ingest.series import BUY, DEFAULT_SERIES, SELL, codes

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def client() -> BCRPClient:
    return BCRPClient(retry=RetryPolicy(max_attempts=3, base_delay=2.0))


def test_both_series_codes_exist_and_align(client: BCRPClient) -> None:
    df = client.fetch(codes(DEFAULT_SERIES), date(2026, 9, 1), date(2026, 9, 4))

    assert list(df.columns) == [BUY.code, SELL.code]
    assert len(df) == 4
    assert (df[BUY.code] < df[SELL.code]).all()


def test_september_still_parses(client: BCRPClient) -> None:
    # Guards the "Set" month token: fails loudly if the API changes it to
    # something our month map does not know.
    df = client.fetch([SELL.code], date(2025, 9, 1), date(2025, 9, 30))
    assert {d.month for d in df.index} == {9}


def test_history_starts_in_january_1997(client: BCRPClient) -> None:
    df = client.fetch([SELL.code], date(1996, 12, 1), date(1997, 1, 31))
    assert df.index[0].date() == date(1997, 1, 2)


def test_invalid_code_is_not_json(client: BCRPClient) -> None:
    fast = BCRPClient(retry=RetryPolicy(max_attempts=1))
    with pytest.raises(BCRPUnavailableError, match="non-JSON"):
        fast.fetch(["PD99999PD"], date(2026, 11, 2), date(2026, 11, 6))
