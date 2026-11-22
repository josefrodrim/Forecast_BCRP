"""HTTP client for the BCRPData API ("imperative shell").

Thin layer around httpx: build the URL, perform the GET, classify failures
and retry the transient ones. All parsing/validation is delegated to the pure
``parse`` module.

Failure taxonomy (verified in notebooks/01_api):

- Transient -> retried with exponential backoff + full jitter:
  timeouts, network errors, HTTP 429 / 5xx, and **non-JSON bodies**. The API
  sits behind an Imperva WAF whose challenge page arrives as ``200 text/html``,
  so a non-JSON body may be a temporary block.
- Permanent -> raised immediately: other HTTP 4xx (``BCRPRequestError``) and
  JSON whose content breaks the contract (``BCRPParseError`` from ``parse``).

Retrying a GET is safe because it is idempotent: repeating it has no side
effects on the server.
"""

import json
import logging
import random
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from types import TracebackType
from typing import Self

import httpx
import pandas as pd

from fxcast.ingest.parse import parse_response

logger = logging.getLogger(__name__)

BASE_URL = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
_SNIPPET_CHARS = 120


class BCRPTransientError(Exception):
    """A failure that may succeed if retried (network, 5xx, 429, non-JSON)."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class BCRPRequestError(Exception):
    """A permanent HTTP error (4xx other than 429): the request itself is wrong."""


class BCRPUnavailableError(Exception):
    """All retry attempts were exhausted on transient errors."""


@dataclass(frozen=True)
class RetryPolicy:
    """How many times to try, and how long to wait between attempts."""

    max_attempts: int = 5
    base_delay: float = 1.0  # seconds; cap for attempt n is base * 2**(n-1)
    max_delay: float = 30.0  # never wait longer than this between attempts

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.base_delay < 0 or self.max_delay < 0:
            raise ValueError("delays must be >= 0")


def backoff_delay(attempt: int, policy: RetryPolicy, rng: random.Random) -> float:
    """Exponential backoff with *full jitter* for the given failed attempt (1-based).

    Full jitter = uniform(0, cap). Without jitter, many clients that failed at
    the same moment would retry in lockstep and hit the server together again
    (thundering herd); randomizing spreads them out.
    """
    cap = min(policy.max_delay, policy.base_delay * 2 ** (attempt - 1))
    return rng.uniform(0.0, cap)


def build_url(codes: Sequence[str], start: date, end: date, base_url: str = BASE_URL) -> str:
    """``{base}/{CODE1-CODE2}/json/{start}/{end}/ing`` (``/ing`` = English labels)."""
    if not codes:
        raise ValueError("At least one series code is required")
    return f"{base_url}/{'-'.join(codes)}/json/{start.isoformat()}/{end.isoformat()}/ing"


class BCRPClient:
    """Fetch BCRP series with retries.

    Dependencies are injectable so tests run instantly and offline:
    ``http`` (e.g. an ``httpx.Client`` with ``MockTransport``), ``sleep`` (a
    no-op recorder instead of ``time.sleep``) and ``rng`` (a seeded RNG).
    """

    def __init__(
        self,
        *,
        http: httpx.Client | None = None,
        retry: RetryPolicy | None = None,
        sleep: Callable[[float], None] = time.sleep,
        rng: random.Random | None = None,
        base_url: str = BASE_URL,
        timeout: float = 30.0,
    ) -> None:
        # Only close the httpx.Client if we created it (ownership rule).
        self._owns_http = http is None
        self._http = http if http is not None else httpx.Client(timeout=timeout)
        self._retry = retry if retry is not None else RetryPolicy()
        self._sleep = sleep
        self._rng = rng if rng is not None else random.Random()
        self._base_url = base_url

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_http:
            self._http.close()

    def fetch(self, codes: Sequence[str], start: date, end: date) -> pd.DataFrame:
        """Download and parse ``codes`` for ``[start, end]`` into a DataFrame."""
        payload = self.fetch_payload(codes, start, end)
        # Parse errors are permanent: deliberately outside the retry loop.
        return parse_response(payload, codes, start, end)

    def fetch_payload(self, codes: Sequence[str], start: date, end: date) -> object:
        """GET the raw decoded JSON, retrying transient failures."""
        url = build_url(codes, start, end, self._base_url)
        policy = self._retry

        for attempt in range(1, policy.max_attempts + 1):
            try:
                return self._get_json(url)
            except BCRPTransientError as exc:
                if attempt == policy.max_attempts:
                    raise BCRPUnavailableError(
                        f"BCRP API unavailable after {attempt} attempts: {exc}"
                    ) from exc
                delay = backoff_delay(attempt, policy, self._rng)
                if exc.retry_after is not None:  # server knows best (429)
                    delay = max(delay, min(exc.retry_after, policy.max_delay))
                logger.warning(
                    "Attempt %d/%d failed (%s); retrying in %.1fs",
                    attempt,
                    policy.max_attempts,
                    exc,
                    delay,
                )
                self._sleep(delay)

        raise AssertionError("unreachable")  # loop always returns or raises

    def _get_json(self, url: str) -> object:
        """One attempt: classify every failure as transient or permanent."""
        try:
            response = self._http.get(url)
        except httpx.TimeoutException as exc:  # subclass of TransportError: check first
            raise BCRPTransientError(f"timeout: {exc!r}") from exc
        except httpx.TransportError as exc:  # DNS, connection reset, TLS...
            raise BCRPTransientError(f"network error: {exc!r}") from exc

        status = response.status_code
        if status == 429 or status >= 500:
            raise BCRPTransientError(f"HTTP {status}", retry_after=_parse_retry_after(response))
        if status >= 400:
            raise BCRPRequestError(f"HTTP {status} for {url}")

        # Content-Type is always text/html (even for good JSON), so it cannot
        # tell data from a WAF page: try to decode instead.
        try:
            decoded: object = json.loads(response.content)
        except ValueError as exc:  # JSONDecodeError and UnicodeDecodeError
            snippet = response.text[:_SNIPPET_CHARS].replace("\n", " ")
            raise BCRPTransientError(
                f"expected JSON, got non-JSON body (invalid series code or WAF block?): {snippet!r}"
            ) from exc
        return decoded


def _parse_retry_after(response: httpx.Response) -> float | None:
    """``Retry-After`` in seconds, if the server sent a numeric one."""
    value = response.headers.get("retry-after")
    try:
        return float(value) if value is not None else None
    except ValueError:  # HTTP-date form: ignore, fall back to backoff
        return None
