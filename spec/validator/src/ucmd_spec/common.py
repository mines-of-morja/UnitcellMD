"""Checks shared by all validators: spec version and JSON Schema."""

from __future__ import annotations

import json
import re
from functools import cache
from typing import Any

from jsonschema import Draft202012Validator

from .paths import schema_path
from .report import Invalid

_SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")

#: (major, minor) accepted by this reader. While major == 0 the minor must match exactly
#: (system-package.md §9).
SUPPORTED = (0, 1)


def check_spec_version(value: Any) -> None:
    if not isinstance(value, str) or not _SEMVER.match(value):
        raise Invalid("E_VERSION", f"spec_version must be a semver string, got {value!r}")
    major, minor, _patch = (int(part) for part in value.split("."))
    if (major, minor) != SUPPORTED:
        raise Invalid(
            "E_VERSION",
            f"spec_version {value} is not supported by this reader "
            f"(supports {SUPPORTED[0]}.{SUPPORTED[1]}.x)",
        )


@cache
def _validator(name: str) -> Draft202012Validator:
    schema = json.loads(schema_path(name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)


def check_schema(document: Any, name: str) -> None:
    """Raise ``E_SCHEMA`` with up to five messages if ``document`` violates schema ``name``."""
    errors = sorted(_validator(name).iter_errors(document), key=lambda e: list(e.absolute_path))
    if errors:
        shown = "; ".join(
            f"{'/' + '/'.join(str(p) for p in e.absolute_path)}: {e.message}" for e in errors[:5]
        )
        more = f" (+{len(errors) - 5} more)" if len(errors) > 5 else ""
        first = "/" + "/".join(str(p) for p in errors[0].absolute_path)
        raise Invalid("E_SCHEMA", shown + more, first)
