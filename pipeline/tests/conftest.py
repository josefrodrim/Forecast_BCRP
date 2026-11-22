"""Shared pytest fixtures."""

import json
from collections.abc import Callable
from pathlib import Path

import pytest

BCRP_FIXTURES = Path(__file__).parent / "fixtures" / "bcrp"


@pytest.fixture
def bcrp_payload() -> Callable[[str], object]:
    """Factory: load a recorded BCRP JSON response, decoded as the client would."""

    def _load(name: str) -> object:
        raw = (BCRP_FIXTURES / f"{name}.json").read_bytes()
        decoded: object = json.loads(raw)
        return decoded

    return _load


@pytest.fixture
def bcrp_raw() -> Callable[[str], bytes]:
    """Factory: raw bytes of a recorded response, e.g. ``bcrp_raw("invalid_code.html")``."""

    def _load(filename: str) -> bytes:
        return (BCRP_FIXTURES / filename).read_bytes()

    return _load
