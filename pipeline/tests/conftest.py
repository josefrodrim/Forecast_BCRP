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
