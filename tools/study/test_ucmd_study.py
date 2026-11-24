"""Tests of the study driver with a fake builder and a fake engine (no MD is run).

ucmd-builder/.venv/bin/pytest tools/study      # any Python ≥ 3.11 with pytest
"""

from __future__ import annotations

import json
import os
import stat
import sys
import time
import tomllib
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import ucmd_study as us

FAKE = r'''#!{python}
"""Fake ucmd / ucmd-build for the study tests."""
import json, os, sys, tomllib
from pathlib import Path
args = sys.argv[1:]
log = Path(os.environ["FAKE_LOG"])
with log.open("a") as fh:
    fh.write(" ".join([Path(sys.argv[0]).name] + args) + "\n")
if args == ["--version"]:
    print("ucmd 0.0.0 (fake)" if Path(sys.argv[0]).name == "ucmd" else "ucmd-builder fake")
    sys.exit(0)
cmd = args[0]
if cmd == "build":   # ucmd-build build recipe.toml -o built.ucsys
    out = Path(args[3]); out.mkdir()
    (out / "system.json").write_text(json.dumps({"atom_count": 12}))
elif cmd == "check":
    sys.exit(0)
elif cmd == "minimize":
    out = Path(args[3]); out.mkdir()
    (out / "system.json").write_text(json.dumps({"atom_count": 12}))
elif cmd == "run":
    doc = tomllib.loads(Path(args[1]).read_text())
    T = doc["thermostat"]["temperature_K"]
    out = Path("out"); out.mkdir(exist_ok=True)
    stop_at = int(os.environ.get("FAKE_STOP_AT", "-1"))
    hang_at = int(os.environ.get("FAKE_HANG_AT", "-1"))
    restart = "--restart" in args
    start = 50 if restart else 0
    mode = "a" if restart else "w"
    with (out / "thermo.tsv").open(mode) as fh:
        if not restart:
            fh.write("# step\ttime_ps\tpotential_kjmol\ttotal_kjmol\tconserved_energy_kjmol"
                     "\ttemperature_K\tpressure_bar\n")
        for step in range(start, doc["run"]["steps"] + 1, 10):
            if step == stop_at and not restart:
                (out / "checkpoint.ucchk").write_text("ckpt")
                sys.exit(143)
            if step == hang_at and not restart:  # a hung GPU: no output, no exit
                fh.flush()
                (out / "checkpoint.ucchk").write_text("ckpt")
                import signal, subprocess, time
                signal.signal(signal.SIGTERM, signal.SIG_IGN)  # stuck: only SIGKILL ends it
                helper = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(600)"])
                Path(os.environ["FAKE_HELPER_PID"]).write_text(str(helper.pid))
                time.sleep(600)
            fh.write(f"{step}\t{step / 1000}\t-5.0\t-1.0\t-1.0\t{T}\t{T - 300}\n")
    (out / "checkpoint.ucchk").write_text("ckpt")
sys.exit(0)
'''


@pytest.fixture
def study(tmp_path: Path, monkeypatch) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name in ("ucmd", "ucmd-build"):
        exe = bin_dir / name
        exe.write_text(FAKE.replace("{python}", sys.executable))
        exe.chmod(exe.stat().st_mode | stat.S_IXUSR)
    profile = tmp_path / "machine.toml"
    profile.write_text(
        f'[executables]\nucmd = "{bin_dir / "ucmd"}"\nucmd-build = "{bin_dir / "ucmd-build"}"\n'
    )
    monkeypatch.setenv("UCMD_MACHINE_PROFILE", str(profile))
    monkeypatch.setenv("FAKE_LOG", str(tmp_path / "calls.log"))
    monkeypatch.delenv("FAKE_STOP_AT", raising=False)
    monkeypatch.delenv("FAKE_HANG_AT", raising=False)
    monkeypatch.setenv("FAKE_HELPER_PID", str(tmp_path / "helper.pid"))
    studies = tmp_path / "studies"
    monkeypatch.setattr(us, "STUDIES", studies)
    recipes = tmp_path / "recipes"
    recipes.mkdir()
    for name in ("mixa_1.0M", "mixa_0.5M", "mixb_1.0M"):
        (recipes / f"{name}.toml").write_text(f'name = "{name}"\n')
    d = studies / "2026-01-01_test"
    d.mkdir(parents=True)
    text = (
        (Path(us.WORKSPACE) / "studies/2026-11-17_ec-temperature-scan/study.toml")
        .read_text()
        .replace('"../../ucmd-builder/examples/EC/recipes/*.toml"', '"../../recipes/*.toml"')
        .replace("temperature_C = [-10, 0, 10, 20, 30, 40, 50]", "temperature_C = [-10, 20]")
        .replace("steps = 10000", "steps = 100")
    )
    (d / "study.toml").write_text(text)
    return d


def test_toml_writer_round_trips() -> None:
    doc = {
        "a": 1,
        "b": 2.0,
        "c": 'x"y',
        "d": [1.5, 2.5],
        "t": {"e": True, "u": {"f": 1e-5}},
        "p": [{"kind": "x", "v": 1}, {"kind": "y"}],
    }
    assert tomllib.loads(us.to_toml(doc)) == doc


def test_plan_order_seeds_and_run_toml(study: Path) -> None:
    s = us.load_study(study)
    ids = [t.id for t in s.tasks]
    # priority: 1.0 M first (both mixtures, both temperatures), then 0.5 M
    assert ids == [
        "mixa_1.0M/T-10C",
        "mixa_1.0M/T20C",
        "mixb_1.0M/T-10C",
        "mixb_1.0M/T20C",
        "mixa_0.5M/T-10C",
        "mixa_0.5M/T20C",
    ]
    task = s.tasks[0]
    assert task.system.labels == {"mixture": "mixa", "concentration_M": "1.0"}
    assert task.temperature_K == 263.15
    doc = tomllib.loads(us.run_toml(s, task))
    assert doc["system"] == "../../../systems/mixa_1.0M/minimized.ucsys"
    assert doc["velocities"]["temperature_K"] == doc["thermostat"]["temperature_K"] == 263.15
    assert doc["run"]["seed"] == us.seed_of(s, task)
    assert doc["providers"] == [
        {"kind": "force-field", "cutoff_nm": 1.4, "coulomb": "pme", "ewald_tolerance": 1e-5}
    ]
    # the seed depends on the run id only
    assert len({us.seed_of(s, t) for t in s.tasks}) == len(s.tasks)


def test_run_index_views_and_resume(study: Path, monkeypatch) -> None:
    monkeypatch.setenv("FAKE_STOP_AT", "50")  # every first attempt stops at step 50
    assert us.main(["run", str(study), "--nice", "0", "--max-runs", "1"]) == 0
    first = study / "runs/mixa_1.0M/T-10C"
    assert json.loads((first / "status.json").read_text())["state"] == "stopped"
    monkeypatch.setenv("FAKE_STOP_AT", "-1")
    assert us.main(["run", str(study), "--nice", "0"]) == 0
    status = json.loads((first / "status.json").read_text())
    assert status["state"] == "done" and status["seed"] == us.seed_of(
        us.load_study(study), us.load_study(study).tasks[0]
    )
    calls = (study.parents[1] / "calls.log").read_text()
    assert "run run.toml --restart out/checkpoint.ucchk" in calls  # continued, not restarted
    assert calls.count("ucmd-build build") == 3  # each system built once
    assert calls.count("minimize minimize.toml") == 3  # and minimized once
    summary = status["summary"]
    assert summary["temperature_K"]["mean"] == pytest.approx(263.15)
    assert summary["window_ps"] == [0.05, 0.1]
    index = json.loads((study / "index.json").read_text())
    assert index["counts"] == {"done": 6}
    text = (study / "INDEX.md").read_text()
    assert "6 of 6 runs done" in text and "### mixa" in text
    link = study / "views/by-temperature/T20C/mixb_1.0M"
    assert link.is_symlink() and link.resolve() == (study / "runs/mixb_1.0M/T20C").resolve()
    assert (study / "views/by-mixture/mixa/0.5M/T-10C/run.toml").is_file()
    assert "2026-01-01_test" in (us.STUDIES / "CATALOG.md").read_text()
    # a second driver run does nothing
    before = calls.count("\n")
    assert us.main(["run", str(study), "--nice", "0"]) == 0
    assert (study.parents[1] / "calls.log").read_text().count("\n") == before + 2  # --version


def test_a_changed_plan_is_refused_for_existing_runs(study: Path) -> None:
    assert us.main(["run", str(study), "--nice", "0", "--max-runs", "1"]) == 0
    toml = study / "study.toml"
    toml.write_text(toml.read_text().replace("tau_ps = 0.1", "tau_ps = 0.5"))
    first = study / "runs/mixa_1.0M/T-10C"
    status = json.loads((first / "status.json").read_text())
    status["state"] = "stopped"  # pretend it must continue
    (first / "status.json").write_text(json.dumps(status))
    us.main(["run", str(study), "--nice", "0", "--max-runs", "1"])
    status = json.loads((first / "status.json").read_text())
    assert status["state"] == "failed" and "differs from study.toml" in status["reason"]


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    # a zombie (killed, not yet reaped by its parent) counts as gone
    stat_file = Path(f"/proc/{pid}/stat")
    return not (stat_file.exists() and stat_file.read_text().split(") ")[1].startswith("Z"))


def test_the_watchdog_ends_a_hung_run_and_the_next_run_continues_it(
    study: Path, monkeypatch
) -> None:
    monkeypatch.setenv("FAKE_HANG_AT", "50")
    monkeypatch.setattr(us, "KILL_GRACE_S", 2.0)
    assert us.main(["run", str(study), "--nice", "0", "--stall-minutes", "0.02"]) == 0
    first = study / "runs/mixa_1.0M/T-10C"
    status = json.loads((first / "status.json").read_text())
    assert status["state"] == "stalled" and "watchdog" in status["reason"]
    # the whole process group is ended, including what the engine started (the container)
    helper = int((study.parents[1] / "helper.pid").read_text())
    time.sleep(0.2)
    assert not _alive(helper)
    # the study stops after a stall instead of hanging on the next run
    assert not (study / "runs/mixa_1.0M/T20C/status.json").exists()
    log = (study / "logs/driver.log").read_text()
    assert "watchdog: no output" in log and "stopping the study after a stall" in log
    # the next driver continues the stalled run from its checkpoint
    monkeypatch.setenv("FAKE_HANG_AT", "-1")
    assert us.main(["run", str(study), "--nice", "0", "--max-runs", "1"]) == 0
    status = json.loads((first / "status.json").read_text())
    assert status["state"] == "done" and "reason" not in status
    calls = (study.parents[1] / "calls.log").read_text()
    assert calls.count("run run.toml --restart out/checkpoint.ucchk") == 1


def test_retry_failed_continues_from_the_checkpoint(study: Path) -> None:
    assert us.main(["run", str(study), "--nice", "0", "--max-runs", "1"]) == 0
    first = study / "runs/mixa_1.0M/T-10C"
    status = json.loads((first / "status.json").read_text())
    status.update(state="failed", reason="engine exit 125; see run.log")
    (first / "status.json").write_text(json.dumps(status))
    us.main(["run", str(study), "--nice", "0", "--max-runs", "1"])  # skipped without the flag
    calls = (study.parents[1] / "calls.log").read_text()
    assert "--restart" not in calls
    us.main(["run", str(study), "--nice", "0", "--max-runs", "1", "--retry-failed"])
    calls = (study.parents[1] / "calls.log").read_text()
    assert "run run.toml --restart out/checkpoint.ucchk" in calls
    status = json.loads((first / "status.json").read_text())
    assert status["state"] == "done" and "reason" not in status


def test_a_fresh_restart_of_a_failed_run_drops_the_old_reason(study: Path) -> None:
    """EC rung, 2026-11-21: a run that failed before its first checkpoint starts afresh with
    --retry-failed; it finished (exit 0) but status.json still said "engine exit 1"."""
    assert us.main(["run", str(study), "--nice", "0", "--max-runs", "1"]) == 0
    first = study / "runs/mixa_1.0M/T-10C"
    (first / "out" / "checkpoint.ucchk").unlink()  # no checkpoint: the next attempt is fresh
    status = json.loads((first / "status.json").read_text())
    status.update(state="failed", reason="engine exit 1; see run.log", exit=1)
    (first / "status.json").write_text(json.dumps(status))
    us.main(["run", str(study), "--nice", "0", "--max-runs", "1", "--retry-failed"])
    calls = (study.parents[1] / "calls.log").read_text()
    assert "--restart" not in calls
    status = json.loads((first / "status.json").read_text())
    assert status["state"] == "done" and status["exit"] == 0
    assert "reason" not in status
    # the index shows no reason for a done run either
    index = json.loads((study / "index.json").read_text())
    done = [r for r in index["runs"] if r["state"] == "done"]
    assert done and all("reason" not in r for r in done)


def test_summary_skips_rows_without_a_value(tmp_path: Path) -> None:
    thermo = tmp_path / "thermo.tsv"
    thermo.write_text(
        "# step\ttime_ps\ttemperature_K\tpressure_bar\tvolume_nm3\n"
        "0\t0.0\t300\t5.0\t80.0\n"
        "1\t1.0\t300\tnan\t80.0\n"
        "2\t2.0\t300\t1.0\t80.0\n"
        "3\t3.0\t300\tnan\t80.0\n"
        "4\t4.0\t300\t3.0\t80.0\n"
    )
    s = us.summarize(thermo)  # the second half: t = 2, 3, 4
    assert s["rows"] == 3
    assert s["pressure_bar"]["mean"] == pytest.approx(2.0)
    assert s["pressure_bar"]["sd"] == pytest.approx(2.0**0.5)
    assert s["temperature_K"]["mean"] == pytest.approx(300.0)


def test_a_second_driver_is_refused(study: Path) -> None:
    (study / "driver.pid").write_text(f"{os.getpid()}\n")
    with pytest.raises(SystemExit, match="already running"):
        us.main(["run", str(study), "--nice", "0"])


def test_system_mass_from_molecule_types_and_counts() -> None:
    doc = {
        "molecule_types": {
            "Li": {"atoms": [{"mass_amu": 6.941}]},
            "W": {"atoms": [{"mass_amu": 15.999}, {"mass_amu": 1.008}, {"mass_amu": 1.008}]},
        },
        "components": [{"molecule_type": "Li", "count": 2}, {"molecule_type": "W", "count": 10}],
    }
    assert us.system_mass_amu(doc) == pytest.approx(2 * 6.941 + 10 * 18.015)
    assert us.system_mass_amu({"atom_count": 3}) is None


def test_a_study_from_ready_packages_skips_build_and_minimization(study: Path) -> None:
    pkgs = study / "packages"
    (pkgs / "box_1.0M.ucsys").mkdir(parents=True)
    (pkgs / "box_1.0M.ucsys" / "system.json").write_text(json.dumps({"atom_count": 12}))
    toml = study / "study.toml"
    text = toml.read_text().replace(
        'recipes = "../../recipes/*.toml"', 'packages = "packages/*.ucsys"'
    )
    toml.write_text(text)
    assert us.main(["run", str(study), "--nice", "0"]) == 0
    calls = (study.parents[1] / "calls.log").read_text()
    assert "ucmd-build build" not in calls and "minimize" not in calls
    status = json.loads((study / "systems/box_1.0M/status.json").read_text())
    assert status["state"] == "minimized" and status["package"] == "packages/box_1.0M.ucsys"
    assert json.loads((study / "runs/box_1.0M/T-10C/status.json").read_text())["state"] == "done"
