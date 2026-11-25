"""Tests of the queue dashboard (docs/design/queue.md, step 1): fixtures, no GPU, no docker."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import ucmd_queue as q


def make_run(study: Path, rid: str, state: str, steps: int = 1000, at: int | None = None) -> None:
    d = study / "runs" / rid
    (d / "out").mkdir(parents=True)
    (d / "status.json").write_text(json.dumps({"id": rid, "state": state}))
    (d / "run.toml").write_text(f"[run]\nsteps = {steps}\n")
    if at is not None:
        rows = "\n".join(f"{k}\t{k * 0.001}\t0\t0" for k in (at - 1, at))
        (d / "out" / "thermo.tsv").write_text("# step\ttime\n" + rows + "\n")


def make_study(root: Path, name: str, runs: list[tuple[str, str]], plan: bool = True) -> Path:
    study = root / name
    study.mkdir(parents=True)
    (study / "study.toml").write_text('[study]\nquestion = "a question"\n')
    if plan:
        ids = [{"id": rid} for rid, _ in runs]
        (study / "index.json").write_text(json.dumps({"runs": ids}))
    return study


@pytest.fixture
def collector(tmp_path: Path) -> q.Collector:
    studies = tmp_path / "studies"
    s = make_study(
        studies,
        "2026-01-01_scan",
        [("a/T1", "done"), ("b/T1", "running"), ("c/T1", "pending"), ("d/T1", "stopped")],
    )
    make_run(s, "a/T1", "done")
    make_run(s, "b/T1", "running", steps=1000, at=250)
    make_run(s, "d/T1", "stopped")
    make_study(studies, "2026-01-02_old", [("x/T1", "pending")])
    cfg = {
        "node": {
            "name": "test",
            "studies_dir": str(studies),
            "tasks_file": str(tmp_path / "tasks.toml"),
        }
    }
    return q.Collector(cfg)


def test_running_run_with_progress_is_orphaned_without_a_driver(collector) -> None:
    doc = collector.collect()
    (run,) = doc["running"]
    assert run["run"] == "b/T1"
    assert run["step"] == 250 and run["steps"] == 1000
    assert run["fraction"] == pytest.approx(0.25)
    assert run["orphan"] is True  # nothing holds driver.pid


def test_a_live_driver_makes_the_run_running_and_the_rest_next(collector) -> None:
    study = collector.studies_dir / "2026-01-01_scan"
    (study / "driver.pid").write_text(str(os.getpid()))
    procs = {os.getpid(): "python ucmd_study.py run"}
    errors: list[str] = []
    studies = q.inspect_studies(collector.studies_dir, procs, errors)
    scan = next(s for s in studies if s["name"] == "2026-01-01_scan")
    assert scan["driver_pid"] == os.getpid()
    nxt = q.build_next(studies, [])
    assert [(n["run"], n["state"]) for n in nxt] == [("c/T1", "pending"), ("d/T1", "stopped")]
    assert [n["rank"] for n in nxt] == [1, 2]


def test_studies_with_open_runs_and_no_one_to_start_them_are_unscheduled(collector) -> None:
    doc = collector.collect()
    by = {s["name"]: s for s in doc["studies"]}
    assert by["2026-01-02_old"]["unscheduled"] is True
    assert by["2026-01-02_old"]["counts"] == {"pending": 1}
    assert doc["next"] == []  # unscheduled work is never presented as "next"


def test_unreadable_status_is_reported_not_replaced(collector) -> None:
    bad = collector.studies_dir / "2026-01-01_scan" / "runs" / "d" / "T1" / "status.json"
    bad.write_text("{not json")
    doc = collector.collect()
    assert any("status.json" in e for e in doc["errors"])
    by = {s["name"]: s for s in doc["studies"]}
    assert by["2026-01-01_scan"]["counts"].get("stopped") is None  # the run is not counted as ok


def test_missing_everything_still_gives_a_document(tmp_path: Path) -> None:
    doc = q.Collector({"node": {"studies_dir": str(tmp_path / "none")}}).collect()
    assert doc["schema"] == 1 and doc["studies"] == [] and doc["running"] == []
    assert [r["kind"] for r in doc["resources"]][-1] == "cpu"


def test_missing_telemetry_is_reported(tmp_path: Path) -> None:
    errors: list[str] = []
    assert q.telemetry(tmp_path / "nope.tsv", errors) is None
    assert errors


def test_telemetry_row(tmp_path: Path) -> None:
    f = tmp_path / "t.tsv"
    f.write_text(
        "time_utc\tedge_C\tpower_W\tcap_W\tbusy_pct\n2020-01-01T00:00:00Z\t40\t88\t120\t81\n"
    )
    out = q.telemetry(f, [])
    assert out is not None
    assert out["power_W"] == 88.0 and out["age_s"] > 1e6


def test_eta_needs_a_minute_and_a_restart_resets_it() -> None:
    h = q.History()
    assert h.rate_ps_per_s("k", 0.0, 100.0) is None
    assert h.rate_ps_per_s("k", 30.0, 130.0) is None  # less than a minute of history
    assert h.rate_ps_per_s("k", 120.0, 220.0) == pytest.approx(1.0)
    assert h.rate_ps_per_s("k", 130.0, 50.0) is None  # went back: restarted from a checkpoint


def test_queue_scripts_waiting_state(tmp_path: Path) -> None:
    (tmp_path / "gpu-queue7.sh").write_text(
        "#!/usr/bin/env bash\n# queue 7: a scan\nfor S in studies/2026-01-01_scan; do :; done\n"
    )
    stamp = q.now_iso()
    log = tmp_path / "resume.log"
    log.write_text(f"{stamp}  queue 7 waits for other GPU queues (pids 1)\n")
    cfg = {"dir": str(tmp_path), "log": str(log)}
    procs = [(123, "bash /x/gpu-queue7.sh")]
    (item,) = q.queue_scripts(cfg, procs, [])
    assert item["state"] == "waiting" and item["studies"] == ["2026-01-01_scan"]
    assert item["number"] == 7
    log.write_text("2020-01-01T00:00:00Z  queue 7 waits for other GPU queues (pids 1)\n")
    (item,) = q.queue_scripts(cfg, procs, [])
    assert item["state"] == "active"


def test_unreachable_remote_does_not_disturb_the_local_node(collector) -> None:
    cache = q.Cache(collector, [{"name": "far", "url": "http://127.0.0.1:9"}], 1000.0)
    cache.refresh()
    snap = cache.snapshot()
    assert snap["node"] == "test" and snap["studies"]
    (remote,) = snap["remotes"]
    assert remote["node"] == "far" and remote["reachable"] is False


def test_tasks_wait_for_their_predecessors_and_faults_are_reported(collector, tmp_path) -> None:
    assert collector.collect()["tasks"] == []  # no file: no tasks, no error
    (tmp_path / "tasks.toml").write_text(
        '[[task]]\nid = "A"\nstate = "open"\n'
        '[[task]]\nid = "B"\nstate = "open"\nafter = ["A"]\n'
        '[[task]]\nid = "C"\nstate = "nonsense"\n'
        '[[task]]\nid = "D"\nstate = "open"\nafter = ["missing"]\n'
    )
    doc = collector.collect()
    assert {t["id"]: t["state"] for t in doc["tasks"]} == {
        "A": "open",
        "B": "waiting",
        "D": "waiting",
    }
    assert any("'C'" in e for e in doc["errors"]) and any("missing" in e for e in doc["errors"])
    (tmp_path / "tasks.toml").write_text("[[task]\n")
    doc = collector.collect()
    assert doc["tasks"] == [] and any("tasks.toml" in e for e in doc["errors"])


def test_the_task_file_of_the_repository_is_valid() -> None:
    errors: list[str] = []
    assert q.read_tasks(q.REPO / "docs" / "tasks.toml", errors)
    assert errors == []
