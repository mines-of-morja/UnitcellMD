"""The job spool of the queue (docs/design/queue.md, step 2): files, one lock, no daemon.

A job is a JSON file `<spool>/jobs/<id>.json`. Everything that changes a job happens under one
`flock` on `<spool>/.lock`, so the CLI, the server and several workers can work on the same spool.

Priority: a larger number goes first; equal priorities go in submit order. Times: ISO UTC for
display, epoch seconds (`heartbeat_ts`) for arithmetic.
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import secrets
import time
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

KINDS = ("study", "command")
ACTIVE = ("claimed", "running")
FINISHED = ("done", "failed", "cancelled")
HEARTBEAT_TIMEOUT_S = 120.0

NAME = re.compile(r"^[\w.\-]+$")
RUN_ID = re.compile(r"^[\w.\-+]+/[\w.\-+]+$")


class JobError(ValueError):
    """A request that cannot be honoured (unknown job, wrong state, bad field)."""


def _now() -> tuple[str, float]:
    t = time.time()
    return datetime.fromtimestamp(t, UTC).strftime("%Y-%m-%dT%H:%M:%SZ"), t


class Spool:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        (self.root / "jobs").mkdir(parents=True, exist_ok=True)

    @contextmanager
    def locked(self):
        with (self.root / ".lock").open("a") as fh:
            fcntl.flock(fh, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(fh, fcntl.LOCK_UN)

    # -- storage (call under the lock when changing) ---------------------------------------
    def _path(self, job_id: str) -> Path:
        if not NAME.match(job_id):
            raise JobError(f"bad job id {job_id!r}")
        return self.root / "jobs" / f"{job_id}.json"

    def _read(self, path: Path) -> dict:
        return json.loads(path.read_text())

    def _write(self, job: dict) -> None:
        path = self._path(job["id"])
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(job, indent=2) + "\n")
        os.replace(tmp, path)

    def get(self, job_id: str) -> dict:
        try:
            return self._read(self._path(job_id))
        except FileNotFoundError:
            raise JobError(f"no such job: {job_id}") from None

    def jobs(self) -> list[dict]:
        out = []
        for p in sorted((self.root / "jobs").glob("*.json")):
            try:
                out.append(self._read(p))
            except (OSError, ValueError):
                continue  # a half-written file never appears: writes are atomic; others are not ours
        return sorted(out, key=lambda j: (j.get("submitted_ts", 0.0), j["id"]))

    # -- submit ----------------------------------------------------------------------------
    def submit(
        self,
        *,
        kind: str,
        needs: str,
        title: str = "",
        priority: int = 0,
        first: bool = False,
        study: str | None = None,
        runs: list[str] | None = None,
        argv: list[str] | None = None,
        after: list[str] | None = None,
        submitted_by: str = "",
        note: str = "",
    ) -> dict:
        if kind not in KINDS:
            raise JobError(f"kind must be one of {KINDS}")
        if not NAME.match(needs or ""):
            raise JobError("needs must be a resource tag such as gpu-hip-mixed or cpu")
        if isinstance(priority, bool) or not isinstance(priority, int):
            raise JobError("priority must be an integer")
        if kind == "study":
            if not study or not NAME.match(study):
                raise JobError("a study job needs the study folder name")
            if runs is not None and (not runs or not all(RUN_ID.match(r) for r in runs)):
                raise JobError("runs must be ids like base_s1/T20C")
            argv = None
        else:
            if not argv or not all(isinstance(a, str) and a for a in argv):
                raise JobError("a command job needs a non-empty argv list of strings")
            study, runs = None, None
        with self.locked():
            existing = {j["id"]: j for j in self.jobs()}
            for a in after or []:
                if a not in existing:
                    raise JobError(f"'after' names an unknown job: {a}")
            if first:
                queued = [j["priority"] for j in existing.values() if j["state"] == "queued"]
                priority = max(queued + [priority]) + 1
            iso, ts = _now()
            job = {
                "id": f"j{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(2)}",
                "kind": kind,
                "title": title or (study if kind == "study" else " ".join(argv or [])[:60]),
                "needs": needs,
                "priority": priority,
                "study": study,
                "runs": runs,
                "argv": argv,
                "after": list(after or []),
                "state": "queued",
                "submitted": iso,
                "submitted_ts": ts,
                "submitted_by": submitted_by,
                "claimed_by": None,
                "claimed_at": None,
                "heartbeat": None,
                "heartbeat_ts": None,
                "progress": None,
                "cancel_requested": False,
                "held": False,
                "hold_requested": False,
                "requeued": 0,
                "finished": None,
                "exit": None,
                "note": note,
            }
            self._write(job)
        return job

    # -- scheduling ------------------------------------------------------------------------
    def requeue_stale(self, timeout_s: float = HEARTBEAT_TIMEOUT_S) -> list[str]:
        """Jobs whose worker has been silent for `timeout_s` go back to the queue."""
        out = []
        with self.locked():
            now = time.time()
            for job in self.jobs():
                if job["state"] in ACTIVE and now - (job["heartbeat_ts"] or 0) > timeout_s:
                    iso, _ = _now()
                    job.update(
                        state="queued",
                        requeued=job["requeued"] + 1,
                        note=f"requeued {iso}: {job['claimed_by']} stopped answering",
                        claimed_by=None,
                        claimed_at=None,
                        heartbeat=None,
                        heartbeat_ts=None,
                        cancel_requested=False,
                        held=job.get("held", False) or job.get("hold_requested", False),
                        hold_requested=False,
                    )
                    self._write(job)
                    out.append(job["id"])
        return out

    def _eligible(self, job: dict, worker: dict, jobs: list[dict]) -> bool:
        if job["state"] != "queued" or job.get("held"):
            return False
        if job["needs"] not in worker.get("provides", []):
            return False
        if job["kind"] == "command" and not worker.get("allow_command"):
            return False
        by_id = {j["id"]: j for j in jobs}
        if any(by_id.get(a, {}).get("state") != "done" for a in job["after"]):
            return False
        # one driver per study: its lock file is per study
        return not (
            job["kind"] == "study"
            and any(
                j["state"] in ACTIVE and j["kind"] == "study" and j["study"] == job["study"]
                for j in jobs
            )
        )

    def claim(self, worker: dict) -> dict | None:
        """The best queued job this worker may take, now held by it; None if there is none."""
        self.requeue_stale()
        with self.locked():
            if self.control(str(worker.get("name"))).get("paused"):
                return None
            jobs = self.jobs()
            ready = [j for j in jobs if self._eligible(j, worker, jobs)]
            if not ready:
                return None
            ready.sort(key=lambda j: (-j["priority"], j.get("submitted_ts", 0.0), j["id"]))
            job = ready[0]
            iso, ts = _now()
            job.update(
                state="claimed",
                claimed_by=worker["name"],
                claimed_at=iso,
                heartbeat=iso,
                heartbeat_ts=ts,
                note="",
            )
            self._write(job)
            return job

    def _held(self, job_id: str, worker: str) -> dict:
        job = self.get(job_id)
        if job["state"] not in ACTIVE or job["claimed_by"] != worker:
            raise JobError(f"{job_id} is not held by {worker} (state {job['state']})")
        return job

    def heartbeat(self, job_id: str, worker: str, progress: dict | None = None) -> dict:
        """Keeps the claim alive; the answer tells the worker to cancel if asked to."""
        with self.locked():
            job = self._held(job_id, worker)
            iso, ts = _now()
            job.update(state="running", heartbeat=iso, heartbeat_ts=ts)
            if progress is not None:
                job["progress"] = progress
            self._write(job)
            return {
                "cancel": bool(job["cancel_requested"]),
                "hold": bool(job.get("hold_requested")),
            }

    def finish(
        self, job_id: str, worker: str, state: str, exit_code: int | None, note: str
    ) -> dict:
        if state not in FINISHED:
            raise JobError(f"state must be one of {FINISHED}")
        with self.locked():
            job = self._held(job_id, worker)
            job.update(state=state, exit=exit_code, note=note, finished=_now()[0])
            self._write(job)
            return job

    def release(self, job_id: str, worker: str, note: str) -> dict:
        """The worker gives the job back (e.g. the GPU was needed elsewhere); it keeps its place."""
        with self.locked():
            job = self._held(job_id, worker)
            job.update(
                state="queued",
                claimed_by=None,
                claimed_at=None,
                heartbeat=None,
                heartbeat_ts=None,
                cancel_requested=False,
                held=job.get("held", False) or job.get("hold_requested", False),
                hold_requested=False,
                note=note,
            )
            self._write(job)
            return job

    # -- control ---------------------------------------------------------------------------
    def cancel(self, job_id: str) -> dict:
        with self.locked():
            job = self.get(job_id)
            if job["state"] == "queued":
                job.update(
                    state="cancelled", finished=_now()[0], note="cancelled before it started"
                )
            elif job["state"] in ACTIVE:
                job["cancel_requested"] = True  # the worker stops it gracefully and reports back
                job["note"] = "cancel requested"
            else:
                raise JobError(f"{job_id} is already {job['state']}")
            self._write(job)
            return job

    def set_priority(self, job_id: str, priority: int) -> dict:
        if isinstance(priority, bool) or not isinstance(priority, int):
            raise JobError("priority must be an integer")
        with self.locked():
            job = self.get(job_id)
            if job["state"] != "queued":
                raise JobError(f"{job_id} is {job['state']}; only queued jobs change priority")
            job["priority"] = priority
            self._write(job)
            return job

    def hold(self, job_id: str) -> dict:
        """Stop: a queued job waits; a running one is stopped by its worker (checkpoint) and
        then waits. `resume` continues it."""
        with self.locked():
            job = self.get(job_id)
            if job["state"] == "queued":
                job.update(held=True, note="stopped; waits for Continue")
            elif job["state"] in ACTIVE:
                job.update(hold_requested=True, note="stop requested")
            else:
                raise JobError(f"{job_id} is already {job['state']}")
            self._write(job)
            return job

    def resume(self, job_id: str) -> dict:
        with self.locked():
            job = self.get(job_id)
            if job["state"] in FINISHED:
                raise JobError(f"{job_id} is already {job['state']}")
            job.update(held=False, hold_requested=False, note="")
            self._write(job)
            return job

    # -- controls of a worker: free its computer, limit its threads -------------------------
    def _control_path(self, worker: str) -> Path:
        if not NAME.match(worker or ""):
            raise JobError(f"bad worker name {worker!r}")
        return self.root / "workers" / f"{worker}.json"

    def control(self, worker: str) -> dict:
        """{paused, threads}; threads None: the worker's own setting."""
        out = {"paused": False, "threads": None}
        try:
            out.update(json.loads(self._control_path(worker).read_text()))
        except (OSError, JobError):
            pass
        return out

    def set_control(self, worker: str, **kw) -> dict:
        """`paused`: bool; `threads`: positive int, or None for the worker's own setting."""
        path = self._control_path(worker)
        if set(kw) - {"paused", "threads"}:
            raise JobError("a worker has the controls 'paused' and 'threads'")
        if "paused" in kw and not isinstance(kw["paused"], bool):
            raise JobError("paused must be true or false")
        t = kw.get("threads")
        if t is not None and (isinstance(t, bool) or not isinstance(t, int) or not 1 <= t <= 1024):
            raise JobError("threads must be a positive integer or null")
        with self.locked():
            new = {**self.control(worker), **kw}
            path.parent.mkdir(exist_ok=True)
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(new) + "\n")
            os.replace(tmp, path)
        return new
