import json

from conftest import FIXTURES

from ucmd_spec.cli import main


def test_exit_codes_and_json_output(capsys) -> None:
    assert main(["validate", str(FIXTURES / "valid" / "argon-864")]) == 0
    assert main(["validate", str(FIXTURES / "invalid" / "net-charge"), "--json"]) == 1
    out = json.loads(capsys.readouterr().out.split("\n", 1)[1])
    assert out["ok"] is False and out["issues"][0]["code"] == "E_NET_CHARGE"
    assert main(["validate-run", str(FIXTURES / "runs" / "argon-nvt.toml"), "--with-system"]) == 0
    assert main(["version"]) == 0
