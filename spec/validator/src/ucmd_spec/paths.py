"""Locate the spec directory (schemas, fixtures)."""

from __future__ import annotations

import os
from pathlib import Path


def spec_dir() -> Path:
    """``$UCMD_SPEC_DIR`` if set, else ``spec/`` of the checkout this package lives in."""
    env = os.environ.get("UCMD_SPEC_DIR")
    if env:
        return Path(env).resolve()
    # spec/validator/src/ucmd_spec/paths.py -> parents[3] == spec/
    return Path(__file__).resolve().parents[3]


def schema_path(name: str) -> Path:
    return spec_dir() / "schemas" / f"{name}.schema.json"
