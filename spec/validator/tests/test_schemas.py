import json

import pytest
from jsonschema import Draft202012Validator

from ucmd_spec.paths import schema_path


@pytest.mark.parametrize("name", ["system", "run-config"])
def test_schema_is_a_valid_draft_2020_12_schema(name: str) -> None:
    schema = json.loads(schema_path(name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
