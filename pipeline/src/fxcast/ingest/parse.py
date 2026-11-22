"""Pure parsing of BCRPData API responses.

"Functional core": no network, no disk, no clock. Every function here maps
inputs to outputs (or raises), so it is fully testable with recorded fixtures.
The HTTP client (imperative shell) lives in ``client.py``.

Behaviors handled here were verified by probing the API (notebooks/01_api):

- Dates look like ``"02.Nov.26"``: 2-digit year, and September is ``"Set"``
  even when English is requested, so ``strptime("%b")`` cannot be used.
- Values are strings; ``"n.d."`` marks missing data.
- The API returns the full Mon-Fri grid of the requested range: holidays,
  dates before the series starts and dates not yet published all come as
  ``"n.d."``.
- With several series, ``values`` is positional w.r.t. ``config.series``.
"""

import math
from collections.abc import Sequence
from datetime import date

import pandas as pd

# Own month map instead of locale-dependent "%b". "Set" (Spanish) is what the
# API actually sends for September; "Sep" is accepted in case it is fixed.
MONTHS: dict[str, int] = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Set": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}

MISSING_MARKERS: frozenset[str] = frozenset({"n.d."})


class BCRPParseError(ValueError):
    """The response is valid JSON but its content is not what we expect.

    This is a *permanent* error: retrying will not help, the API contract
    changed (or the request was wrong). The pipeline must fail loudly.
    """


def parse_date(raw: str, start: date, end: date) -> date:
    """Parse ``"DD.Mon.YY"`` resolving the century inside ``[start, end]``.

    The requested range is a free invariant: every returned date must fall
    inside it. Using it to pick the century avoids Python's ``%y`` pivot
    (``68 -> 2068``, ``69 -> 1969``) and catches any misparse.
    """
    parts = raw.split(".")
    if len(parts) != 3:
        raise BCRPParseError(f"Unexpected date format {raw!r} (expected 'DD.Mon.YY')")
    day_s, month_s, year_s = parts

    month = MONTHS.get(month_s)
    if month is None:
        raise BCRPParseError(f"Unknown month token {month_s!r} in date {raw!r}")
    if not (day_s.isdigit() and year_s.isdigit() and len(year_s) == 2):
        raise BCRPParseError(f"Unexpected date format {raw!r} (expected 'DD.Mon.YY')")

    candidates: list[date] = []
    for century in (1900, 2000):
        try:
            candidate = date(century + int(year_s), month, int(day_s))
        except ValueError:  # e.g. 29.Feb in a non-leap year of that century
            continue
        if start <= candidate <= end:
            candidates.append(candidate)

    if len(candidates) != 1:
        raise BCRPParseError(
            f"Date {raw!r} does not resolve to exactly one date in [{start}, {end}]"
        )
    return candidates[0]


def parse_value(raw: str) -> float:
    """Parse a value string: known missing markers -> NaN, else a finite float.

    Deliberately strict (no ``errors="coerce"``): a format change such as a
    decimal comma must fail loudly, not turn into silent NaNs.
    """
    text = raw.strip()
    if text in MISSING_MARKERS:
        return math.nan
    try:
        value = float(text)
    except ValueError as exc:
        raise BCRPParseError(f"Non-numeric value {raw!r}") from exc
    # float() also accepts "nan" / "inf": never valid exchange rates.
    if not math.isfinite(value):
        raise BCRPParseError(f"Non-finite value {raw!r}")
    return value


def parse_response(
    payload: object,
    codes: Sequence[str],
    start: date,
    end: date,
) -> pd.DataFrame:
    """Turn a decoded BCRPData payload into a tidy DataFrame.

    Returns one float64 column per series code, indexed by a ``date`` index
    (tz-naive, daily), sorted and unique. Interior ``n.d.`` rows (holidays)
    are kept as NaN; leading/trailing all-``n.d.`` rows (before the series
    starts / not yet published) are dropped.
    """
    if not codes:
        raise ValueError("At least one series code is required")
    if start > end:
        raise ValueError(f"start ({start}) must not be after end ({end})")

    periods = _extract_periods(payload, n_series=len(codes))

    dates: list[date] = []
    rows: list[list[float]] = []
    for period in periods:
        name, values = period
        parsed_date = parse_date(name, start, end)
        if dates and parsed_date <= dates[-1]:
            raise BCRPParseError(f"Dates not strictly increasing: {parsed_date} after {dates[-1]}")
        dates.append(parsed_date)
        rows.append([parse_value(v) for v in values])

    frame = pd.DataFrame(
        rows,
        index=pd.DatetimeIndex(dates, name="date"),
        columns=list(codes),
        dtype="float64",
    )
    return _trim_missing_edges(frame)


def _extract_periods(payload: object, n_series: int) -> list[tuple[str, list[str]]]:
    """Validate the payload shape and return ``(name, values)`` pairs."""
    if not isinstance(payload, dict):
        raise BCRPParseError(f"Expected a JSON object, got {type(payload).__name__}")

    config = payload.get("config")
    series = config.get("series") if isinstance(config, dict) else None
    if not isinstance(series, list):
        raise BCRPParseError("Missing 'config.series' list")
    if len(series) != n_series:
        raise BCRPParseError(f"Requested {n_series} series, response describes {len(series)}")

    periods = payload.get("periods")
    if not isinstance(periods, list):
        raise BCRPParseError("Missing 'periods' list")

    result: list[tuple[str, list[str]]] = []
    for i, period in enumerate(periods):
        name = period.get("name") if isinstance(period, dict) else None
        values = period.get("values") if isinstance(period, dict) else None
        if not isinstance(name, str) or not isinstance(values, list):
            raise BCRPParseError(f"Malformed period at index {i}: {period!r}")
        # Values are positional: a length mismatch would silently misalign
        # buying and selling rates.
        if len(values) != n_series or not all(isinstance(v, str) for v in values):
            raise BCRPParseError(f"Period {name!r}: expected {n_series} string values")
        result.append((name, values))
    return result


def _trim_missing_edges(frame: pd.DataFrame) -> pd.DataFrame:
    """Drop leading and trailing rows where every series is NaN."""
    has_data = frame.notna().any(axis=1)
    if not has_data.any():
        return frame.iloc[0:0]
    first = has_data.idxmax()
    last = has_data[::-1].idxmax()
    return frame.loc[first:last]
