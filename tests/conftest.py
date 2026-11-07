from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> Any:
    """Load and parse a JSON fixture by filename."""
    path = FIXTURES_DIR / filename
    if not path.is_file():
        raise FileNotFoundError(f"Fixture not found: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def fixture_loader() -> Callable[[str], Any]:
    """Provide a fixture loading callable."""
    return load_fixture


@pytest.fixture
def devices_v1_json() -> dict[str, Any]:
    """Return raw parsed V1 devices payload."""
    return load_fixture("devices_v1.json")


@pytest.fixture
def channels_v1_json() -> list[dict[str, Any]]:
    """Return raw parsed V1 channels payload."""
    return load_fixture("channels_v1.json")


@pytest.fixture
def sites_v1_json() -> dict[str, Any]:
    """Return raw parsed V1 sites payload."""
    return load_fixture("sites_v1.json")


@pytest.fixture
def devices_legacy_json() -> dict[str, Any]:
    """Return raw parsed legacy devices payload."""
    return load_fixture("devices_legacy.json")


@pytest.fixture
def usages_v1_json() -> dict[str, Any]:
    """Return raw parsed V1 usages payload."""
    return load_fixture("usages_v1.json")


@pytest.fixture
def evse_control_v1_json() -> dict[str, Any]:
    """Return raw parsed V1 EVSE control payload."""
    return load_fixture("evse_control_v1.json")


@pytest.fixture
def evses_v1_json() -> dict[str, Any]:
    """Return raw parsed V1 EVSEs list payload."""
    return load_fixture("evses_v1.json")


@pytest.fixture
def excess_generation_v1_json() -> dict[str, Any]:
    """Return raw parsed V1 excess generation payload."""
    return load_fixture("excess_generation_v1.json")
