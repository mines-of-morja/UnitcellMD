"""Command-line interface: ``ucmd-spec validate | validate-run | validate-trajectory | version``."""

from __future__ import annotations

import argparse
import json
import sys

from . import SPEC_VERSION, __version__
from .report import Report
from .run_config import validate_run_config
from .system import validate_system_package


def _emit(report: Report, as_json: bool) -> int:
    if as_json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(f"{'OK' if report.ok else 'INVALID'}  {report.target}")
        for issue in report.issues:
            where = f"  ({issue.location})" if issue.location else ""
            print(f"  {issue.code}  {issue.message}{where}")
    return 0 if report.ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ucmd-spec", description="Validate UnitcellMD files.")
    sub = parser.add_subparsers(dest="command", required=True)
    p_sys = sub.add_parser("validate", help="validate a system package directory")
    p_sys.add_argument("package")
    p_run = sub.add_parser("validate-run", help="validate a run.toml")
    p_run.add_argument("run_toml")
    p_run.add_argument(
        "--with-system", action="store_true", help="also validate the referenced package"
    )
    p_trj = sub.add_parser("validate-trajectory", help="validate an H5MD trajectory (needs h5py)")
    p_trj.add_argument("file")
    for p in (p_sys, p_run, p_trj):
        p.add_argument("--json", action="store_true", help="machine-readable output")
    sub.add_parser("version", help="print validator and spec version")
    args = parser.parse_args(argv)

    if args.command == "version":
        print(f"ucmd-spec {__version__} (spec {SPEC_VERSION})")
        return 0
    if args.command == "validate":
        return _emit(validate_system_package(args.package), args.json)
    if args.command == "validate-run":
        return _emit(validate_run_config(args.run_toml, with_system=args.with_system), args.json)
    from .trajectory import validate_trajectory

    return _emit(validate_trajectory(args.file), args.json)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
