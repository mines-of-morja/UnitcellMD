"""Reading rule of the 3 M map on made-up numbers (written before the runs)."""

import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("map3", Path(__file__).with_name("analyze.py"))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


@pytest.mark.parametrize(
    ("r", "expected"),
    [(3.0, "scales with the salt"), (2.0, "scales with the salt"), (1.7, "partly"), (1.5, "does not scale with the salt"),
     (0.4, "does not scale with the salt")],
)  # fmt: skip
def test_ratio_verdict(r, expected):
    assert a.ratio_verdict(r) == expected
