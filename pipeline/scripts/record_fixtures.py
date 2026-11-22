"""Record real BCRPData API responses as test fixtures.

Fixtures are *recorded*, never hand-written: they capture the API's real
quirks (text/html Content-Type, "Set" for September, n.d. grids, HTML error
pages) that a hand-made sample would silently miss.

Run (from pipeline/):  uv run python scripts/record_fixtures.py
Re-run only when you deliberately want to refresh the fixtures; review the
diff, since tests may need updating if the API changed.
"""

import json
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

BASE_URL = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"
FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "bcrp"
PAUSE_SECONDS = 3.0  # be polite with a public API (and its WAF)

# name -> (series codes, start, end, why this case exists)
CASES: dict[str, tuple[str, str, str, str]] = {
    "two_series_september": (
        "PD04637PD-PD04638PD",
        "2026-09-01",
        "2026-09-04",
        "Two series (positional values) and the 'Set' month token",
    ),
    "fiestas_patrias": (
        "PD04638PD",
        "2026-07-24",
        "2026-07-31",
        "Interior n.d. on national holidays (27-29 Jul) that must be kept as NaN",
    ),
    "trailing_unpublished": (
        "PD04638PD",
        "2026-11-16",
        "2026-11-27",
        "Trailing n.d. for dates not yet published (recorded on 2026-11-22)",
    ),
    "series_start": (
        "PD04638PD",
        "1996-12-25",
        "1997-01-10",
        "Leading n.d. before the series starts (first value 02.Jan.97)",
    ),
    "weekend_empty": (
        "PD04638PD",
        "2026-11-21",
        "2026-11-22",
        "Weekend-only range: valid JSON with an empty periods list",
    ),
    "invalid_code": (
        "PD99999PD",
        "2026-11-02",
        "2026-11-06",
        "Invalid code: HTTP 200 with an HTML page instead of JSON",
    ),
}


def main() -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict[str, str | int]] = {}

    with httpx.Client(timeout=30.0) as client:
        for name, (codes, start, end, why) in CASES.items():
            url = f"{BASE_URL}/{codes}/json/{start}/{end}/ing"
            response = client.get(url)
            is_json = response.content.lstrip().startswith(b"{")
            path = FIXTURES_DIR / f"{name}.{'json' if is_json else 'html'}"
            # Raw bytes, untouched: the exact payload the client will see.
            path.write_bytes(response.content)
            manifest[name] = {
                "file": path.name,
                "url": url,
                "why": why,
                "status": response.status_code,
                "content_type": response.headers.get("content-type", ""),
                "recorded_at": datetime.now(UTC).isoformat(timespec="seconds"),
            }
            print(f"{name:<22} {response.status_code} {len(response.content):>6} B -> {path.name}")
            time.sleep(PAUSE_SECONDS)

    (FIXTURES_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
