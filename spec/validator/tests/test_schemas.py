import json

import pytest
from jsonschema import Draft202012Validator

from ucmd_spec.paths import schema_path


@pytest.mark.parametrize("name", ["system", "run-config"])
def test_schema_is_a_valid_draft_2020_12_schema(name: str) -> None:
    schema = json.loads(schema_path(name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_a_reader_without_pair_overrides_fails_closed() -> None:
    """0.1.2: the 0.1.1 schema (no pair_overrides) rejects a package that uses them (ADR 0015)."""
    from conftest import FIXTURES, load_system

    schema = json.loads(schema_path("system").read_text(encoding="utf-8"))
    ff = schema["$defs"]["forcefield"]
    assert ff["additionalProperties"] is False
    del ff["properties"]["pair_overrides"]
    doc = load_system(FIXTURES / "valid" / "kob-andersen-500")
    errors = list(Draft202012Validator(schema).iter_errors(doc))
    assert errors and any("pair_overrides" in e.message for e in errors)
