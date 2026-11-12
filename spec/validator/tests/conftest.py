from __future__ import annotations

import json
from pathlib import Path

import pytest

from ucmd_spec.paths import spec_dir

FIXTURES = spec_dir() / "fixtures"


@pytest.fixture
def fixtures() -> Path:
    return FIXTURES


def load_system(package: Path) -> dict:
    return json.loads((package / "system.json").read_text(encoding="utf-8"))
