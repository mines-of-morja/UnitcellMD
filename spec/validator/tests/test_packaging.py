"""The built wheel carries the JSON Schemas (gate-b1a.md section 4.1)."""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

VALIDATOR = Path(__file__).resolve().parents[1]


def test_wheel_contains_the_schemas(tmp_path):
    pytest.importorskip("hatchling")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "wheel",
            "--no-deps",
            "--no-build-isolation",
            "-w",
            str(tmp_path),
            str(VALIDATOR),
        ],
        check=True,
        capture_output=True,
    )
    wheel = next(tmp_path.glob("ucmd_spec-*.whl"))
    names = zipfile.ZipFile(wheel).namelist()
    assert "ucmd_spec/schemas/system.schema.json" in names
    assert "ucmd_spec/schemas/run-config.schema.json" in names
