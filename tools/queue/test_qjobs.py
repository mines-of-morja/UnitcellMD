"""Tests of the job spool: ordering, claims, cancellation, stale workers."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
import qjobs as qj

GPU = {"name": "gpu-a", "provides": ["gpu-hip-mixed"], "allow_command": False}
LOCAL = {"name": "ws", "provides": ["gpu-hip-mixed", "cpu"], "allow_command": True}


@pytest.fixture
def spool(tmp_path: Path) -> qj.Spool:
    return qj.Spool(tmp_path / "queue")


def study_job(spool, study="2026-01-01_a", **kw):
    return spool.submit(kind="study", needs="gpu-hip-mixed", study=study, **kw)


def test_priority_then_submit_order(spool) -> None:
    a = study_job(spool, "s_a")
    b = study_job(spool, "s_b", priority=5)
    c = study_job(spool, "s_c", priority=5)
    order = []
    for _ in range(3):
        job = spool.claim(GPU)
        order.append(job["study"])
        spool.finish(job["id"], "gpu-a", "done", 0, "")
    assert order == ["s_b", "s_c", "s_a"]
    assert {a["id"], b["id"], c["id"]} == {j["id"] for j in spool.jobs()}


def test_first_goes_before_everything_queued(spool) -> None:
    study_job(spool, "s_a", priority=9)
    urgent = study_job(spool, "s_b", first=True)
    assert urgent["priority"] == 10
    assert spool.claim(GPU)["study"] == "s_b"


def test_a_worker_only_gets_what_it_provides_and_may_run(spool) -> None:
    spool.submit(kind="study", needs="cpu", study="s_cpu")
    spool.submit(kind="command", needs="gpu-hip-mixed", argv=["echo", "hi"])
    assert spool.claim(GPU) is None  # no cpu tag; commands need allow_command
    assert spool.claim(LOCAL)["kind"] == "study"  # submit order
    assert spool.claim(LOCAL)["kind"] == "command"  # the worker that may run commands takes it


def test_one_driver_per_study(spool) -> None:
    study_job(spool, "s_a", runs=["x/T1"])
    study_job(spool, "s_a", runs=["y/T1"])
    first = spool.claim(GPU)
    assert first["runs"] == ["x/T1"]
    assert spool.claim({**GPU, "name": "gpu-b"}) is None  # same study is busy
    spool.finish(first["id"], "gpu-a", "done", 0, "")
    assert spool.claim({**GPU, "name": "gpu-b"})["runs"] == ["y/T1"]


def test_after_waits_for_done_not_for_failed(spool) -> None:
    first = study_job(spool, "s_a")
    second = study_job(spool, "s_b", after=[first["id"]])
    job = spool.claim(GPU)
    assert job["id"] == first["id"]
    assert spool.claim(GPU) is None
    spool.finish(job["id"], "gpu-a", "failed", 1, "x")
    assert spool.claim(GPU) is None  # a failed predecessor never releases the job
    assert spool.get(second["id"])["state"] == "queued"


def test_cancel_queued_and_running(spool) -> None:
    a = study_job(spool, "s_a")
    spool.cancel(a["id"])
    assert spool.get(a["id"])["state"] == "cancelled"
    b = study_job(spool, "s_b")
    job = spool.claim(GPU)
    assert job["id"] == b["id"]
    assert spool.heartbeat(b["id"], "gpu-a") == {"cancel": False}
    spool.cancel(b["id"])
    assert spool.heartbeat(b["id"], "gpu-a") == {"cancel": True}
    spool.finish(b["id"], "gpu-a", "cancelled", None, "stopped by request")
    with pytest.raises(qj.JobError, match="already"):
        spool.cancel(b["id"])


def test_only_the_holder_may_report(spool) -> None:
    j = study_job(spool)
    spool.claim(GPU)
    with pytest.raises(qj.JobError, match="not held"):
        spool.finish(j["id"], "someone-else", "done", 0, "")
    with pytest.raises(qj.JobError, match="not held"):
        spool.heartbeat(j["id"], "someone-else")


def test_a_silent_worker_loses_the_job_which_keeps_its_place(spool) -> None:
    j = study_job(spool, priority=3)
    spool.claim(GPU)
    spool.heartbeat(j["id"], "gpu-a")
    assert spool.requeue_stale(timeout_s=3600) == []
    time.sleep(0.01)
    assert spool.requeue_stale(timeout_s=0.001) == [j["id"]]
    again = spool.get(j["id"])
    assert again["state"] == "queued" and again["priority"] == 3 and again["requeued"] == 1
    assert "stopped answering" in again["note"]


def test_release_returns_the_job(spool) -> None:
    j = study_job(spool)
    spool.claim(GPU)
    spool.release(j["id"], "gpu-a", "the GPU is needed elsewhere")
    assert spool.get(j["id"])["state"] == "queued"
    assert spool.claim(GPU)["id"] == j["id"]


@pytest.mark.parametrize(
    "kw, message",
    [
        ({"kind": "shell", "needs": "cpu"}, "kind"),
        ({"kind": "study", "needs": "cpu"}, "study folder"),
        ({"kind": "study", "needs": "cpu", "study": "../x"}, "study folder"),
        ({"kind": "study", "needs": "cpu", "study": "s", "runs": ["no-slash"]}, "runs"),
        ({"kind": "study", "needs": "bad tag", "study": "s"}, "needs"),
        ({"kind": "command", "needs": "cpu", "argv": []}, "argv"),
        ({"kind": "study", "needs": "cpu", "study": "s", "priority": "high"}, "priority"),
        ({"kind": "study", "needs": "cpu", "study": "s", "after": ["nope"]}, "unknown job"),
    ],
)
def test_bad_submissions_are_refused(spool, kw, message) -> None:
    with pytest.raises(qj.JobError, match=message):
        spool.submit(**kw)


def test_job_ids_cannot_escape_the_spool(spool) -> None:
    with pytest.raises(qj.JobError):
        spool.get("../../etc/passwd")
