"""Tests of the DMC calibration's reading rule (the dH_vap code is the EMC baseline's, tested there)."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("dmc", Path(__file__).with_name("analyze.py"))
dmc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dmc)


def test_reading_bands():
    assert dmc.reading(0.9) == "shared by the carbonate types"
    assert dmc.reading(0.6) == "shared by the carbonate types"
    assert dmc.reading(0.45) == "partly shared"
    assert dmc.reading(0.3) == "mainly EMC's own"
    assert dmc.reading(-0.2) == "mainly EMC's own"


def test_emc_functions_are_the_baselines():
    assert dmc.emc_dh.dh_vap(10.0, -15000.0, 500, 298.15) > 40.0
