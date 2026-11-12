"""Every valid fixture passes; every invalid fixture fails with exactly its expected code."""

import json

import pytest
from conftest import FIXTURES

from ucmd_spec.run_config import validate_run_config
from ucmd_spec.system import validate_system_package

VALID = sorted(p for p in (FIXTURES / "valid").iterdir() if p.is_dir())
INVALID = sorted(p for p in (FIXTURES / "invalid").iterdir() if p.is_dir())
RUNS = sorted((FIXTURES / "runs").glob("*.toml"))
INVALID_RUNS = json.loads((FIXTURES / "runs" / "invalid" / "expected.json").read_text())


def test_fixture_sets_are_complete() -> None:
    assert {p.name for p in VALID} == {"argon-864", "harmonic-3d", "nacl-crystal", "water-2"}
    assert len(INVALID) >= 19
    assert len(RUNS) >= 2 and len(INVALID_RUNS) >= 5


@pytest.mark.parametrize("package", VALID, ids=lambda p: p.name)
def test_valid_package_passes(package) -> None:
    report = validate_system_package(package)
    assert report.ok, report.error
    assert not report.issues


@pytest.mark.parametrize("package", INVALID, ids=lambda p: p.name)
def test_invalid_package_reports_its_code(package) -> None:
    expected = json.loads((package / "expected.json").read_text())["code"]
    report = validate_system_package(package)
    assert report.error is not None, f"{package.name} unexpectedly valid"
    assert report.error.code == expected, report.error


def test_every_error_code_of_the_spec_has_a_fixture() -> None:
    codes = {json.loads((p / "expected.json").read_text())["code"] for p in INVALID}
    assert codes == {
        "E_JSON",
        "E_FORMAT",
        "E_VERSION",
        "E_UNITS",
        "E_SCHEMA",
        "E_REFERENCE",
        "E_INDEX",
        "E_ATOM_COUNT",
        "E_CELL",
        "E_ARRAY_MISSING",
        "E_ARRAY_FORMAT",
        "E_NONFINITE",
        "E_PARAMETERS",
        "E_NET_CHARGE",
        "E_MOLECULE_SPLIT",
    }


@pytest.mark.parametrize("run", RUNS, ids=lambda p: p.name)
def test_valid_run_config_passes_with_its_system(run) -> None:
    report = validate_run_config(run, with_system=True)
    assert report.ok, report.error


@pytest.mark.parametrize("name", sorted(INVALID_RUNS), ids=str)
def test_invalid_run_config_reports_its_code(name) -> None:
    report = validate_run_config(FIXTURES / "runs" / "invalid" / name)
    assert report.error is not None and report.error.code == INVALID_RUNS[name], report.error
