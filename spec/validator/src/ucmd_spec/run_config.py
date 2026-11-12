"""Validation of run.toml files (spec/run-config.md §3).

Order: E_TOML, E_VERSION, E_PATH, E_SCHEMA, E_INCOMPATIBLE; with ``with_system`` also the system
package (its own codes) and the run/system cross-checks (E_INCOMPATIBLE).
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

from .common import check_schema, check_spec_version
from .report import Invalid, Report
from .system import validate_system_package

#: Keys holding paths, as key sequences into the parsed document.
PATH_KEYS = (
    ("system",),
    ("output", "directory"),
    ("output", "trajectory", "file"),
    ("output", "thermo", "file"),
    ("output", "checkpoint", "file"),
)


def validate_run_config(path: Path | str, with_system: bool = False) -> Report:
    path = Path(path)
    report = Report(str(path))
    try:
        _validate(path, with_system, report)
    except Invalid as exc:
        report.issues.append(exc.issue)
    return report


def _lookup(doc: dict[str, Any], keys: tuple[str, ...]) -> Any:
    node: Any = doc
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


def _validate(path: Path, with_system: bool, report: Report) -> None:
    try:
        doc = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise Invalid("E_TOML", f"{path.name} is missing", path.name) from exc
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise Invalid("E_TOML", f"{path.name} is not valid TOML ({exc})", path.name) from exc
    check_spec_version(doc.get("spec_version"))
    for keys in PATH_KEYS:
        value = _lookup(doc, keys)
        if isinstance(value, str) and (value.startswith(("/", "~", "\\")) or ":" in value[:3]):
            raise Invalid(
                "E_PATH",
                f"{'.'.join(keys)} = {value!r}: paths must be relative to the run.toml directory",
                "/" + "/".join(keys),
            )
    check_schema(doc, "run-config")

    integrator = doc["run"]["integrator"]
    thermostat = doc.get("thermostat", {}).get("kind")
    if (thermostat == "langevin") != (integrator == "langevin-baoab"):
        raise Invalid(
            "E_INCOMPATIBLE",
            "the langevin thermostat and the langevin-baoab integrator require each other",
            "/thermostat",
        )

    if with_system:
        package = (path.parent / doc["system"]).resolve()
        sub = validate_system_package(package)
        if sub.error is not None:
            raise Invalid(sub.error.code, f"system package {package}: {sub.error.message}")
        system = json.loads((package / "system.json").read_text(encoding="utf-8"))
        periodicity = system["periodicity"]
        if "barostat" in doc and not all(periodicity):
            raise Invalid("E_INCOMPATIBLE", "a barostat needs a fully periodic system", "/barostat")
        if doc.get("momentum", {}).get("remove_angular") and any(periodicity):
            raise Invalid(
                "E_INCOMPATIBLE",
                "remove_angular is not allowed for periodic systems",
                "/momentum/remove_angular",
            )
        report.issues.extend(sub.issues)
