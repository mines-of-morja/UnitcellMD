"""The worker (client) of the queue: takes jobs from a server, runs them with local tools.

    ucmd_queue.py work [--worker NAME] [--config FILE]

One job at a time. The worker asks the server for the best job it can do; it never receives a
command to execute, only data: a `study` job runs this clone's `tools/study/ucmd_study.py` on a
study folder (`--only` the named runs), a `command` job (only if this worker is set to allow it)
runs an argv list in the repo. Machine settings (engine, machine profile per resource tag, the
studies folder, what pauses the GPU) come from the worker's own config, never from the job.

The studies folder must be the server's: on the server machine itself it is `studies/`; on another
computer mount the server's folder (docs: Connect a computer). Results then land in place.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

POLL_S = 15.0
HEARTBEAT_S = 15.0
STOP_WAIT_S = 180.0


class ServerError(RuntimeError):
    """The server answered with an error (code, message) or did not answer."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(f"server {code}: {message}")
        self.code = code


class Api:
    def __init__(self, url: str, token: str, timeout: float = 20.0) -> None:
        self.url, self.token, self.timeout = url.rstrip("/"), token, timeout

    def get(self, path: str) -> dict:
        return self._call(urllib.request.Request(self.url + path, headers=self._headers()))

    def _headers(self) -> dict:
        return {"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"}

    def post(self, path: str, body: dict) -> dict:
        req = urllib.request.Request(
            self.url + path, data=json.dumps(body).encode(), method="POST", headers=self._headers()
        )
        return self._call(req)

    def _call(self, req: urllib.request.Request) -> dict:
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as exc:
            try:
                message = json.load(exc).get("error", "")
            except ValueError:
                message = exc.reason
            raise ServerError(exc.code, str(message)) from None
        except (OSError, ValueError) as exc:
            raise ServerError(0, f"no answer from {self.url}: {exc}") from None


def signal_group(pgid: int, sig: int) -> bool:
    """Send `sig` (0: only probe) to a process group; False if the group is empty."""
    try:
        os.killpg(pgid, sig)
    except ProcessLookupError:
        return False
    return True


def group_roots(pgid: int) -> list[int]:
    """Living members of a process group whose parent is not in the group: the process the job
    started as, and any it left behind when it died."""
    members: dict[int, int] = {}  # pid -> parent pid
    for stat in Path("/proc").glob("[0-9]*/stat"):
        try:
            fields = stat.read_text().rsplit(")", 1)[1].split()
        except OSError:
            continue
        if fields[0] != "Z" and int(fields[2]) == pgid:
            members[int(stat.parent.name)] = int(fields[1])
    return sorted(pid for pid, parent in members.items() if parent not in members)


class Worker:
    def __init__(
        self,
        cfg: dict,
        api: Api,
        repo: Path,
        studies_dir: Path,
        spool_logs: Path,
        guard: Callable[[], str | None],
        paused: Callable[[], str | None],
        progress: Callable[[Path], dict | None],
        log: Callable[[str], None] = print,
    ) -> None:
        self.cfg, self.api, self.repo, self.studies_dir = cfg, api, repo, studies_dir
        self.logs = spool_logs
        self.guard, self.paused, self.progress, self.log = guard, paused, progress, log
        self.name = cfg["name"]
        self.stop_requested = False
        self.stopping = False
        self.signalled: set[int] = set()
        self.child: subprocess.Popen | None = None
        self.study_in_progress: Path | None = None

    # -- identity ----------------------------------------------------------------------------
    def identity(self) -> dict:
        load = os.getloadavg()[0]
        return {
            "name": self.name,
            "provides": list(self.cfg.get("provides", [])),
            "allow_command": bool(self.cfg.get("allow_command", False)),
            "info": {"cores": os.cpu_count(), "load1": round(load, 1), "host": os.uname().nodename},
        }

    # -- main loop ---------------------------------------------------------------------------
    def request_stop(self, *_: object) -> None:
        self.stop_requested = True
        self.stop_child()

    def stop_child(self) -> None:
        """Graceful: a study driver checkpoints the engine; a command gets one SIGTERM and passes
        it on itself (see signal_orphans for what it leaves behind)."""
        if self.child is None or self.child.poll() is not None:
            return
        self.stopping = True
        if self.study_in_progress is not None:
            subprocess.run(
                [sys.executable, str(self.repo / "tools/study/ucmd_study.py"), "stop",
                 str(self.study_in_progress)],
                check=False, capture_output=True,
            )  # fmt: skip
        else:
            self.signalled = set()
            self.signal_orphans()

    def serve(self, once: bool = False) -> None:
        signal.signal(signal.SIGTERM, self.request_stop)
        signal.signal(signal.SIGINT, self.request_stop)
        self.log(f"worker {self.name}: serving {self.api.url}")
        while not self.stop_requested:
            try:
                took = self.step()
            except ServerError as exc:
                self.log(f"worker {self.name}: {exc}")
                took = False
            if once:
                return
            if not took:
                for _ in range(int(POLL_S)):
                    if self.stop_requested:
                        break
                    time.sleep(1.0)

    def step(self) -> bool:
        """One poll: announce, and take a job if nothing local stands in the way."""
        busy = self.guard() or self.paused()
        if busy:
            self.api.post("/api/workers/hello", {"worker": {**self.identity(), "info": {
                **self.identity()["info"], "waiting": busy}}})  # fmt: skip
            return False
        job = self.api.post("/api/claim", {"worker": self.identity()})["job"]
        if job is None:
            return False
        self.log(f"worker {self.name}: took {job['id']} ({job['kind']}: {job['title']})")
        self.run_job(job)
        return True

    # -- running a job -----------------------------------------------------------------------
    def tag_settings(self, needs: str) -> dict:
        return dict(self.cfg.get("tags", {}).get(needs, {}))

    def run_job(self, job: dict) -> None:
        jid = job["id"]
        if job["kind"] == "study":
            built = self.study_command(job)
        else:
            built = self.command_command(job)
        if isinstance(built, str):
            self.finish(jid, "failed", None, built)
            return
        cmd, env, cwd, logfile, study_dir = built
        self.logs.mkdir(parents=True, exist_ok=True)
        released = None
        with logfile.open("ab") as out:
            self.stopping = False
            # its own process group, so that a stop reaches everything the job started
            self.child = subprocess.Popen(
                cmd, env=env, cwd=cwd, stdout=out, stderr=subprocess.STDOUT, start_new_session=True
            )
            self.study_in_progress = study_dir
            cancelled = False
            last = 0.0
            while self.child.poll() is None:
                time.sleep(1.0)
                if self.stop_requested:
                    break
                if time.time() - last < HEARTBEAT_S:
                    continue
                last = time.time()
                why = self.paused()
                if why:
                    released = why
                    self.stop_child()
                    break
                try:
                    prog = self.progress(study_dir) if study_dir else None
                    answer = self.api.post(
                        f"/api/jobs/{jid}/heartbeat", {"worker": self.identity(), "progress": prog}
                    )
                except ServerError as exc:
                    if exc.code == 409:  # the server no longer holds this job for us
                        self.log(f"worker {self.name}: lost {jid}: {exc}")
                        self.stop_child()
                        break
                    continue  # a missed heartbeat is not fatal; the timeout is two minutes
                if answer.get("cancel"):
                    cancelled = True
                    self.stop_child()
                    break
            self.wait_child()
        code = self.child.returncode
        self.child, self.study_in_progress = None, None
        self.report(job, code, cancelled, released)

    def signal_orphans(self) -> None:
        """SIGTERM, once each, to the roots of the job's process group. Never the whole group: a
        study driver takes a second SIGTERM as "kill the engine now" (no stop checkpoint), and an
        engine must only hear from its driver."""
        for pid in group_roots(self.child.pid):
            if pid not in self.signalled:
                self.signalled.add(pid)
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass

    def wait_child(self) -> None:
        """Wait for the job to end; after a stop, for everything in its process group."""
        deadline = time.time() + STOP_WAIT_S
        while self.child.poll() is None or (self.stopping and signal_group(self.child.pid, 0)):
            if self.stopping and self.study_in_progress is None:
                self.child.poll()  # reap, so that what it left behind shows up as orphaned
                self.signal_orphans()
            if time.time() > deadline:
                self.log(f"worker {self.name}: the job does not stop; killing it")
                signal_group(self.child.pid, signal.SIGKILL)
                break
            time.sleep(0.1)
        self.child.wait()

    def study_command(self, job: dict):
        study = self.studies_dir / job["study"]
        if not (study / "study.toml").is_file():
            return f"no study {job['study']} under {self.studies_dir} (mount the server's studies folder)"
        settings = self.tag_settings(job["needs"])
        env = dict(os.environ)
        if settings.get("profile"):
            env["UCMD_MACHINE_PROFILE"] = os.path.expanduser(settings["profile"])
        cmd = [
            sys.executable, str(self.repo / "tools/study/ucmd_study.py"), "run", str(study),
            "--retry-failed", "--stall-minutes", str(self.cfg.get("stall_minutes", 10)),
            "--nice", str(self.cfg.get("nice", 10)),
        ]  # fmt: skip
        if settings.get("ucmd"):
            cmd += ["--ucmd", os.path.expanduser(settings["ucmd"])]
        if job.get("runs"):
            cmd += ["--only", *job["runs"]]
        (study / "logs").mkdir(exist_ok=True)
        return cmd, env, self.repo, study / "logs" / f"worker-{job['id']}.log", study

    def command_command(self, job: dict):
        if not self.cfg.get("allow_command"):
            return "this worker does not run command jobs"
        env = dict(os.environ)
        settings = self.tag_settings(job["needs"])
        if settings.get("profile"):
            env["UCMD_MACHINE_PROFILE"] = os.path.expanduser(settings["profile"])
        return list(job["argv"]), env, self.repo, self.logs / f"{job['id']}.log", None

    # -- reporting ---------------------------------------------------------------------------
    def finish(self, jid: str, state: str, code: int | None, note: str) -> None:
        try:
            self.api.post(
                f"/api/jobs/{jid}/finish",
                {"worker": self.identity(), "state": state, "exit": code, "note": note[:500]},
            )
        except ServerError as exc:
            self.log(f"worker {self.name}: could not report {jid}: {exc}")

    def report(self, job: dict, code: int | None, cancelled: bool, released: str | None) -> None:
        jid = job["id"]
        if released or (self.stop_requested and not cancelled):
            note = f"released: {released or 'worker stopped'}"
            try:
                self.api.post(f"/api/jobs/{jid}/release", {"worker": self.identity(), "note": note})
            except ServerError as exc:
                self.log(f"worker {self.name}: could not release {jid}: {exc}")
            return
        if cancelled:
            return self.finish(jid, "cancelled", code, "stopped by request")
        if job["kind"] == "study":
            states = self.run_states(self.studies_dir / job["study"], job.get("runs"))
            bad = {k: v for k, v in states.items() if v != "done"}
            if code == 0 and not bad:
                return self.finish(jid, "done", 0, f"{len(states)} run(s) done")
            return self.finish(jid, "failed", code, f"exit {code}; not done: {bad or 'none run'}")
        self.finish(jid, "done" if code == 0 else "failed", code, f"exit {code}")

    def run_states(self, study: Path, runs: list[str] | None) -> dict[str, str]:
        """State of each requested run (all of the plan if none are named), from a fresh index."""
        subprocess.run(
            [sys.executable, str(self.repo / "tools/study/ucmd_study.py"), "status", str(study)],
            check=False,
            capture_output=True,
        )
        try:
            listed = json.loads((study / "index.json").read_text())["runs"]
        except (OSError, ValueError, KeyError):
            return {r: "unknown" for r in runs or ["(index unreadable)"]}
        out = {r["id"]: r["state"] for r in listed if runs is None or r["id"] in runs}
        for rid in runs or []:
            out.setdefault(rid, "missing")
        return out
