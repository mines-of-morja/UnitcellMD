"""Tests of the PF6 size map's reading rule."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("pf6", Path(__file__).with_name("analyze.py"))
pf6 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pf6)


def test_reading_bands():
    assert pf6.reading(0.9) == "carries most of the excess"
    assert pf6.reading(0.75) == "carries most of the excess"
    assert pf6.reading(0.5) == "carries part of the excess"
    assert pf6.reading(0.25) == "carries part of the excess"
    assert pf6.reading(0.1) == "carries little of the excess"
    assert pf6.reading(-0.2) == "carries little of the excess"


def test_the_probe_packages_are_the_ones_analysed():
    assert pf6.PROBES == (0.95, 1.05)
