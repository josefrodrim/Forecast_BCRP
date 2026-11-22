"""Tests for fxcast.ingest.client with httpx.MockTransport (no network, no waiting)."""

import random
from collections.abc import Callable
from datetime import date

import httpx
import pytest

from fxcast.ingest.client import (
    BCRPClient,
    BCRPRequestError,
    BCRPUnavailableError,
    RetryPolicy,
    backoff_delay,
    build_url,
)
from fxcast.ingest.parse import BCRPParseError

SELL = "PD04638PD"
START, END = date(2026, 7, 24), date(2026, 7, 31)

Handler = Callable[[httpx.Request], httpx.Response]
LoadRaw = Callable[[str], bytes]


def scripted(*steps: httpx.Response | Exception) -> tuple[Handler, list[httpx.Request]]:
    """A MockTransport handler that plays ``steps`` in order and records requests."""
    calls: list[httpx.Request] = []
    queue = list(steps)

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        step = queue.pop(0)
        if isinstance(step, Exception):
            raise step
        return step

    return handler, calls


def make_client(handler: Handler, sleeps: list[float], max_attempts: int = 4) -> BCRPClient:
    return BCRPClient(
        http=httpx.Client(transport=httpx.MockTransport(handler)),
        retry=RetryPolicy(max_attempts=max_attempts, base_delay=1.0, max_delay=8.0),
        sleep=sleeps.append,  # record delays instead of waiting
        rng=random.Random(42),
    )


def html_200(raw: bytes) -> httpx.Response:
    # Exactly what the API does: 200 + text/html, for JSON and WAF pages alike.
    return httpx.Response(200, content=raw, headers={"content-type": "text/html"})


# --- URL and backoff (pure) ----------------------------------------------------


def test_build_url_joins_codes_and_uses_iso_dates() -> None:
    url = build_url(["PD04637PD", SELL], date(2026, 9, 1), date(2026, 9, 4))
    assert url.endswith("/PD04637PD-PD04638PD/json/2026-09-01/2026-09-04/ing")


@pytest.mark.parametrize(("attempt", "cap"), [(1, 1.0), (2, 2.0), (3, 4.0), (4, 8.0), (9, 8.0)])
def test_backoff_delay_is_within_exponential_cap(attempt: int, cap: float) -> None:
    policy = RetryPolicy(base_delay=1.0, max_delay=8.0)
    rng = random.Random(0)
    delays = [backoff_delay(attempt, policy, rng) for _ in range(200)]
    assert all(0.0 <= d <= cap for d in delays)
    assert max(delays) > cap * 0.8  # jitter actually spreads up to the cap


# --- Happy path ----------------------------------------------------------------


def test_fetch_returns_parsed_frame(bcrp_raw: LoadRaw) -> None:
    handler, calls = scripted(html_200(bcrp_raw("fiestas_patrias.json")))
    sleeps: list[float] = []

    df = make_client(handler, sleeps).fetch([SELL], START, END)

    assert len(calls) == 1
    assert sleeps == []
    assert df[SELL].isna().sum() == 3  # 27-29 Jul holidays kept as NaN


# --- Transient failures are retried ----------------------------------------------


@pytest.mark.parametrize(
    "first_failure",
    [
        "waf_html",
        httpx.Response(503),
        httpx.Response(500),
        httpx.ReadTimeout("read timed out"),
        httpx.ConnectError("connection refused"),
    ],
    ids=["waf-html", "503", "500", "timeout", "connect-error"],
)
def test_transient_failure_then_success(
    first_failure: httpx.Response | Exception | str, bcrp_raw: LoadRaw
) -> None:
    failure = (
        html_200(bcrp_raw("invalid_code.html")) if first_failure == "waf_html" else first_failure
    )
    assert not isinstance(failure, str)
    handler, calls = scripted(failure, html_200(bcrp_raw("fiestas_patrias.json")))
    sleeps: list[float] = []

    df = make_client(handler, sleeps).fetch([SELL], START, END)

    assert len(calls) == 2
    assert len(sleeps) == 1
    assert not df.empty


def test_gives_up_after_max_attempts(bcrp_raw: LoadRaw) -> None:
    waf = bcrp_raw("invalid_code.html")
    handler, calls = scripted(*(html_200(waf) for _ in range(4)))
    sleeps: list[float] = []

    with pytest.raises(BCRPUnavailableError, match=r"after 4 attempts.*non-JSON.*DOCTYPE"):
        make_client(handler, sleeps, max_attempts=4).fetch([SELL], START, END)

    assert len(calls) == 4
    assert len(sleeps) == 3  # no sleep after the last attempt


def test_retry_after_header_is_respected(bcrp_raw: LoadRaw) -> None:
    handler, _ = scripted(
        httpx.Response(429, headers={"retry-after": "5"}),
        html_200(bcrp_raw("fiestas_patrias.json")),
    )
    sleeps: list[float] = []

    make_client(handler, sleeps).fetch([SELL], START, END)

    assert sleeps[0] >= 5.0


# --- Permanent failures are NOT retried ------------------------------------------


def test_client_error_is_not_retried() -> None:
    handler, calls = scripted(httpx.Response(404))
    sleeps: list[float] = []

    with pytest.raises(BCRPRequestError, match="HTTP 404"):
        make_client(handler, sleeps).fetch([SELL], START, END)

    assert len(calls) == 1
    assert sleeps == []


def test_contract_violation_is_not_retried(bcrp_raw: LoadRaw) -> None:
    # Valid JSON for 2 series, but we asked for 1: retrying cannot fix that.
    handler, calls = scripted(html_200(bcrp_raw("two_series_september.json")))
    sleeps: list[float] = []

    with pytest.raises(BCRPParseError):
        make_client(handler, sleeps).fetch([SELL], date(2026, 9, 1), date(2026, 9, 4))

    assert len(calls) == 1
    assert sleeps == []


def test_retry_policy_validates_arguments() -> None:
    with pytest.raises(ValueError, match="max_attempts"):
        RetryPolicy(max_attempts=0)
