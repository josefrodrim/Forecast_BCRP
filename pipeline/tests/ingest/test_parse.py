"""Tests for fxcast.ingest.parse using real recorded BCRP responses."""

import copy
import math
from collections.abc import Callable
from datetime import date

import pandas as pd
import pytest

from fxcast.ingest.parse import BCRPParseError, parse_date, parse_response, parse_value

BUY, SELL = "PD04637PD", "PD04638PD"
WIDE = (date(1990, 1, 1), date(2030, 12, 31))

LoadPayload = Callable[[str], object]


# --- parse_date ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "start", "end", "expected"),
    [
        ("02.Nov.26", *WIDE, date(2026, 11, 2)),
        ("02.Jan.97", *WIDE, date(1997, 1, 2)),
        ("01.Set.26", *WIDE, date(2026, 9, 1)),  # what the API really sends
        ("01.Sep.26", *WIDE, date(2026, 9, 1)),  # accepted in case it is fixed
        # Century comes from the requested range, not from Python's %y pivot:
        ("01.Jan.69", date(2069, 1, 1), date(2069, 12, 31), date(2069, 1, 1)),
        ("31.Dec.68", date(1968, 1, 1), date(1968, 12, 31), date(1968, 12, 31)),
    ],
)
def test_parse_date_valid(raw: str, start: date, end: date, expected: date) -> None:
    assert parse_date(raw, start, end) == expected


@pytest.mark.parametrize(
    ("raw", "match"),
    [
        ("02-Nov-26", "Unexpected date format"),
        ("02.Foo.26", "Unknown month token"),
        ("02.nov.26", "Unknown month token"),  # case-sensitive on purpose
        ("2.Nov.2026", "Unexpected date format"),
        ("30.Feb.26", "does not resolve"),
        ("02.Nov.35", "does not resolve"),  # outside the requested range
    ],
)
def test_parse_date_invalid(raw: str, match: str) -> None:
    with pytest.raises(BCRPParseError, match=match):
        parse_date(raw, *WIDE)


# --- parse_value --------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("3.46057142857143", 3.46057142857143), (" 3.41 ", 3.41), ("2.618", 2.618)],
)
def test_parse_value_numeric(raw: str, expected: float) -> None:
    assert parse_value(raw) == expected


def test_parse_value_missing_marker_is_nan() -> None:
    assert math.isnan(parse_value("n.d."))


@pytest.mark.parametrize("raw", ["3,41", "", "abc", "nan", "inf", "-inf"])
def test_parse_value_rejects_non_numeric_and_non_finite(raw: str) -> None:
    with pytest.raises(BCRPParseError):
        parse_value(raw)


# --- parse_response on recorded fixtures --------------------------------------


def test_two_series_are_aligned_with_codes(bcrp_payload: LoadPayload) -> None:
    df = parse_response(
        bcrp_payload("two_series_september"), [BUY, SELL], date(2026, 9, 1), date(2026, 9, 4)
    )

    assert list(df.columns) == [BUY, SELL]
    assert df.index.name == "date"
    assert list(df.index) == list(pd.bdate_range("2026-09-01", "2026-09-04"))
    assert df.notna().all().all()
    assert (df[BUY] < df[SELL]).all()  # buying rate below selling rate


def test_interior_holidays_are_kept_as_nan(bcrp_payload: LoadPayload) -> None:
    df = parse_response(
        bcrp_payload("fiestas_patrias"), [SELL], date(2026, 7, 24), date(2026, 7, 31)
    )

    holidays = pd.to_datetime(["2026-07-27", "2026-07-28", "2026-07-29"])
    assert df.loc[holidays, SELL].isna().all()
    assert df.index[0] == pd.Timestamp("2026-07-24")
    assert df.index[-1] == pd.Timestamp("2026-07-31")


def test_trailing_unpublished_dates_are_dropped(bcrp_payload: LoadPayload) -> None:
    df = parse_response(
        bcrp_payload("trailing_unpublished"), [SELL], date(2026, 11, 16), date(2026, 11, 27)
    )

    assert df.index[-1] == pd.Timestamp("2026-11-19")  # last published on recording day
    assert df[SELL].notna().all()


def test_leading_dates_before_series_start_are_dropped(bcrp_payload: LoadPayload) -> None:
    df = parse_response(bcrp_payload("series_start"), [SELL], date(1996, 12, 25), date(1997, 1, 10))

    assert df.index[0] == pd.Timestamp("1997-01-02")


def test_empty_periods_return_empty_frame_with_columns(bcrp_payload: LoadPayload) -> None:
    df = parse_response(
        bcrp_payload("weekend_empty"), [SELL], date(2026, 11, 21), date(2026, 11, 22)
    )

    assert df.empty
    assert list(df.columns) == [SELL]


# --- parse_response: contract violations ---------------------------------------


def test_series_count_mismatch_raises(bcrp_payload: LoadPayload) -> None:
    with pytest.raises(BCRPParseError, match="Requested 1 series"):
        parse_response(
            bcrp_payload("two_series_september"), [SELL], date(2026, 9, 1), date(2026, 9, 4)
        )


def test_values_length_mismatch_raises(bcrp_payload: LoadPayload) -> None:
    payload = copy.deepcopy(bcrp_payload("two_series_september"))
    assert isinstance(payload, dict)
    payload["periods"][0]["values"].pop()

    with pytest.raises(BCRPParseError, match="expected 2 string values"):
        parse_response(payload, [BUY, SELL], date(2026, 9, 1), date(2026, 9, 4))


def test_non_increasing_dates_raise(bcrp_payload: LoadPayload) -> None:
    payload = copy.deepcopy(bcrp_payload("fiestas_patrias"))
    assert isinstance(payload, dict)
    payload["periods"].append(payload["periods"][0])  # duplicate first date at the end

    with pytest.raises(BCRPParseError, match="not strictly increasing"):
        parse_response(payload, [SELL], date(2026, 7, 24), date(2026, 7, 31))


@pytest.mark.parametrize(
    "payload",
    [[], "html", {"periods": []}, {"config": {"series": [{}]}}, {"config": {}, "periods": []}],
)
def test_malformed_payload_raises(payload: object) -> None:
    with pytest.raises(BCRPParseError):
        parse_response(payload, [SELL], *WIDE)


def test_invalid_arguments_raise_value_error() -> None:
    with pytest.raises(ValueError, match="At least one series code"):
        parse_response({}, [], *WIDE)
    with pytest.raises(ValueError, match="must not be after"):
        parse_response({}, [SELL], date(2026, 1, 2), date(2026, 1, 1))
