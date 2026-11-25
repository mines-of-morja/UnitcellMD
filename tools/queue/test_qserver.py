"""Tests of the job API, the token rules and a worker that runs a job end to end (fake driver)."""

from __future__ import annotations

import json
import os
import stat
import sys
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest
import qjobs
import qserver
import qworker
import ucmd_queue as q

TOKEN = "s3cret-token"

FAKE_DRIVER = r'''#!{python}
"""Stand-in for tools/study/ucmd_study.py: run / status / stop."""
import json, os, sys, time
from pathlib import Path
cmd, study = sys.argv[1], Path(sys.argv[2])
only = sys.argv[sys.argv.index("--only") + 1:] if "--only" in sys.argv else None
plan = ["a/T1", "b/T1"]
def write(rid, state):
    d = study / "runs" / rid; d.mkdir(parents=True, exist_ok=True)
    (d / "status.json").write_text(json.dumps({{"id": rid, "state": state}}))
if cmd == "run":
    (study / "driver.pid").write_text(str(os.getpid()))
    for rid in plan:
        if only is None or rid in only:
            if os.environ.get("FAKE_HANG"):
                write(rid, "running"); time.sleep(60)
            write(rid, "done" if not os.environ.get("FAKE_FAIL") else "failed")
    (study / "driver.pid").unlink()
elif cmd == "status":
    runs = []
    for rid in plan:
        f = study / "runs" / rid / "status.json"
        runs.append({{"id": rid, "state": json.loads(f.read_text())["state"] if f.exists() else "pending"}})
    (study / "index.json").write_text(json.dumps({{"runs": runs}}))
elif cmd == "stop":
    pass
'''


@pytest.fixture
def env(tmp_path: Path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "tools/study").mkdir(parents=True)
    drv = repo / "tools/study/ucmd_study.py"
    drv.write_text(
        FAKE_DRIVER.replace("{python}", sys.executable).replace("{{", "{").replace("}}", "}")
    )
    drv.chmod(drv.stat().st_mode | stat.S_IXUSR)
    studies = tmp_path / "studies"
    (studies / "2026-01-01_s").mkdir(parents=True)
    (studies / "2026-01-01_s/study.toml").write_text('[study]\nquestion = "q"\n')
    spool = qjobs.Spool(tmp_path / "queue")
    collector = q.Collector({"node": {"name": "test", "studies_dir": str(studies)}})
    registry = qserver.Registry()
    cache = q.Cache(collector, [], 1000.0, spool, registry)
    cache.refresh()
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), qserver.make_handler(cache, b"<html></html>", spool, registry, TOKEN)
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_address[1]}"
    yield {"repo": repo, "studies": studies, "spool": spool, "url": url, "cache": cache,
           "registry": registry, "tmp": tmp_path}  # fmt: skip
    server.shutdown()


def call(url, path, body=None, token=TOKEN, ctype="application/json", method=None):
    headers = {"Content-Type": ctype}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as exc:
        return exc.code, json.load(exc)


def test_get_needs_no_token_from_this_machine_and_state_has_jobs(env) -> None:
    code, doc = call(env["url"], "/api/state", token=None)
    assert code == 200 and doc["node"] == "test" and doc["jobs"] == [] and doc["workers"] == []


@pytest.mark.parametrize(
    "token, ctype, code",
    [(None, "application/json", 401), ("wrong", "application/json", 401),
     (TOKEN, "text/plain", 415)],
)  # fmt: skip
def test_post_needs_the_token_and_json(env, token, ctype, code) -> None:
    got, _ = call(env["url"], "/api/jobs", {"kind": "study"}, token=token, ctype=ctype)
    assert got == code


def test_no_configured_token_refuses_every_post(tmp_path: Path) -> None:
    cache = q.Cache(q.Collector({"node": {"studies_dir": str(tmp_path)}}), [], 1000.0)
    cache.refresh()
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), qserver.make_handler(cache, b"x", None, qserver.Registry(), None)
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}"
        assert call(url, "/api/jobs", {}, token="anything")[0] == 503
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(
                urllib.request.Request(url + "/api/jobs", method="DELETE"), timeout=5
            )
        assert exc.value.code == 405
    finally:
        server.shutdown()


def test_submit_claim_heartbeat_cancel_finish_over_http(env) -> None:
    url = env["url"]
    code, job = call(url, "/api/jobs", {"kind": "study", "needs": "cpu", "study": "2026-01-01_s"})
    assert code == 200 and job["state"] == "queued"
    worker = {"name": "w1", "provides": ["cpu"]}
    code, claim = call(url, "/api/claim", {"worker": worker})
    assert claim["job"]["id"] == job["id"]
    assert call(url, f"/api/jobs/{job['id']}/heartbeat", {"worker": worker})[1] == {"cancel": False}
    call(url, f"/api/jobs/{job['id']}/cancel", {})
    assert call(url, f"/api/jobs/{job['id']}/heartbeat", {"worker": worker})[1] == {"cancel": True}
    other = {"name": "w2", "provides": ["cpu"]}
    code, err = call(url, f"/api/jobs/{job['id']}/finish", {"worker": other, "state": "done"})
    assert code == 409 and "not held" in err["error"]
    code, done = call(
        url, f"/api/jobs/{job['id']}/finish", {"worker": worker, "state": "cancelled"}
    )
    assert done["state"] == "cancelled"
    env["cache"].refresh()
    snap = env["cache"].snapshot()
    assert [w["name"] for w in snap["workers"]] == ["w1", "w2"] and snap["workers"][0]["online"]


def test_a_bad_submission_is_a_409_not_a_crash(env) -> None:
    code, err = call(env["url"], "/api/jobs", {"kind": "shell", "needs": "cpu"})
    assert code == 409 and "kind" in err["error"]


def test_docs_are_served_with_the_server_address(env) -> None:
    (qserver.DOCS).mkdir(exist_ok=True)
    req = urllib.request.Request(env["url"] + "/docs/connect.md")
    with urllib.request.urlopen(req, timeout=5) as r:
        text = r.read().decode()
    assert "{{" not in text and "http://" in text


def make_worker(env, **cfg):
    cfg = {"name": "w1", "provides": ["cpu"], "nice": 0, **cfg}
    api = qworker.Api(env["url"], TOKEN)
    return qworker.Worker(
        cfg, api, env["repo"], env["studies"], env["tmp"] / "logs",
        guard=lambda: None, paused=lambda: None, progress=q.study_progress,
        log=lambda m: None,
    )  # fmt: skip


def test_worker_runs_a_study_job_and_reports_done(env, monkeypatch) -> None:
    monkeypatch.setattr(qworker, "HEARTBEAT_S", 0.0)
    qjobs_job = env["spool"].submit(kind="study", needs="cpu", study="2026-01-01_s", runs=["a/T1"])
    worker = make_worker(env)
    assert worker.step() is True
    job = env["spool"].get(qjobs_job["id"])
    assert job["state"] == "done", job
    assert not (env["studies"] / "2026-01-01_s/runs/b/T1").exists()  # only the named run ran
    assert worker.step() is False  # nothing left


def test_worker_reports_failure_when_a_run_is_not_done(env, monkeypatch) -> None:
    monkeypatch.setenv("FAKE_FAIL", "1")
    j = env["spool"].submit(kind="study", needs="cpu", study="2026-01-01_s")
    make_worker(env).step()
    job = env["spool"].get(j["id"])
    assert job["state"] == "failed" and "not done" in job["note"]


def test_worker_refuses_command_jobs_unless_allowed(env) -> None:
    j = env["spool"].submit(kind="command", needs="cpu", argv=[sys.executable, "-c", "pass"])
    assert make_worker(env).step() is False  # the server never hands it over
    assert env["spool"].get(j["id"])["state"] == "queued"
    worker = make_worker(env, allow_command=True)
    assert worker.step() is True
    assert env["spool"].get(j["id"])["state"] == "done"


def test_a_failing_command_is_failed_with_its_exit_code(env) -> None:
    j = env["spool"].submit(
        kind="command", needs="cpu", argv=[sys.executable, "-c", "raise SystemExit(3)"]
    )
    make_worker(env, allow_command=True).step()
    job = env["spool"].get(j["id"])
    assert job["state"] == "failed" and job["exit"] == 3


def test_a_busy_guard_keeps_the_worker_from_taking_a_job(env) -> None:
    j = env["spool"].submit(kind="study", needs="cpu", study="2026-01-01_s")
    worker = make_worker(env)
    worker.guard = lambda: "2 containers of ucmd-openmm are running"
    assert worker.step() is False
    assert env["spool"].get(j["id"])["state"] == "queued"
    env["cache"].refresh()
    (w,) = env["cache"].snapshot()["workers"]
    assert w["info"]["waiting"].startswith("2 containers")


def test_cancel_stops_a_running_job_and_it_is_reported_cancelled(env, monkeypatch) -> None:
    monkeypatch.setenv("FAKE_HANG", "1")
    monkeypatch.setattr(qworker, "HEARTBEAT_S", 0.0)
    j = env["spool"].submit(kind="command", needs="cpu",
                            argv=[sys.executable, "-c", "import time; time.sleep(30)"])  # fmt: skip
    worker = make_worker(env, allow_command=True)

    def cancel_soon():
        import time

        for _ in range(100):
            if env["spool"].get(j["id"])["state"] == "running":
                env["spool"].cancel(j["id"])
                return
            time.sleep(0.1)

    threading.Thread(target=cancel_soon, daemon=True).start()
    worker.step()
    assert env["spool"].get(j["id"])["state"] == "cancelled"


def test_a_running_run_with_a_worker_driver_is_not_an_orphan(env) -> None:
    study = env["studies"] / "2026-01-01_s"
    d = study / "runs/a/T1"
    d.mkdir(parents=True)
    (d / "status.json").write_text(json.dumps({"id": "a/T1", "state": "running"}))
    (d / "run.toml").write_text("[run]\nsteps = 100\n")
    env["cache"].refresh()
    (run,) = env["cache"].snapshot()["running"]
    assert run["orphan"] is True
    job = env["spool"].submit(kind="study", needs="cpu", study="2026-01-01_s")
    env["spool"].claim({"name": "far", "provides": ["cpu"]})
    env["cache"].refresh()
    (run,) = env["cache"].snapshot()["running"]
    assert run["orphan"] is False and run["worker"] == "far"
    assert job["id"]


def test_the_cli_submits_lists_and_cancels_in_the_local_spool(env, capsys, tmp_path) -> None:
    cfg = tmp_path / "queue.toml"
    cfg.write_text(f'[server]\nspool = "{env["spool"].root}"\n')
    base = ["--config", str(cfg)]
    assert q.main(base + ["submit", "study", "2026-01-01_s", "--needs", "cpu", "--first",
                          "--runs", "a/T1", "--as", "agent-x"]) == 0  # fmt: skip
    (job,) = env["spool"].jobs()
    assert job["submitted_by"] == "agent-x" and job["runs"] == ["a/T1"]
    assert q.main(base + ["jobs"]) == 0 and job["id"] in capsys.readouterr().out
    assert q.main(base + ["priority", job["id"], "7"]) == 0
    assert q.main(base + ["cancel", job["id"]]) == 0
    assert q.main(base + ["cancel", job["id"]]) == 1  # already cancelled: refused, not a traceback
    assert "already" in capsys.readouterr().err


def test_serve_refuses_to_listen_on_the_lan_without_a_token(tmp_path, capsys) -> None:
    cfg = tmp_path / "queue.toml"
    cfg.write_text(f'[server]\nspool = "{tmp_path / "queue"}"\n')
    os.environ.pop("UCMD_QUEUE_TOKEN", None)
    assert q.main(["--config", str(cfg), "serve", "--bind", "0.0.0.0", "--port", "0"]) == 2
    assert "token" in capsys.readouterr().err
