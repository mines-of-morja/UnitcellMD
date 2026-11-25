"""Dashboard of this machine's compute queue: what runs, what waits, what comes next.

    ucmd_queue.py serve [--port 8765] [--bind ADDR]   # dashboard + job API (docs/design/queue.md)
    ucmd_queue.py state                                # the dashboard state as JSON, once
    ucmd_queue.py work [--worker NAME]                 # a worker: take jobs from the server
    ucmd_queue.py submit study|command ... | jobs | cancel JOB | priority JOB N

The page only shows; jobs are changed with the CLI or the token-protected HTTP API
(tools/queue/docs/agents.md). The dashboard reads status.json / thermo.tsv of the studies, the
driver locks, a GPU telemetry file, the process list, `docker ps`, the queue scripts' log and the
task file docs/tasks.toml, and changes nothing. Serves on 127.0.0.1 unless [server] bind and a token are set. Machine-specific settings are in
~/.config/ucmd/queue.toml (see queue.example.toml). Standard library only (Python >= 3.11).

Units: time in s (ETA) or ps (simulated time); the pressure and everything else is not touched.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import re
import subprocess
import sys
import threading
import time
import tomllib
import urllib.request
from datetime import UTC, datetime
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qjobs import ACTIVE, FINISHED, JobError, Spool
from qserver import Registry, make_handler
from qworker import Api, ServerError, Worker

SCHEMA = 1
HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DEFAULT_CONFIG = Path.home() / ".config" / "ucmd" / "queue.toml"
OPEN_STATES = ("pending", "stopped", "failed", "running")
HISTORY_S = 600.0  # window of the ETA estimate
MIN_HISTORY_S = 60.0  # no ETA during the first minute


def now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(path: Path):
    return json.loads(path.read_text())


def tail_lines(path: Path, n: int = 2, block: int = 8192) -> list[str]:
    """The last `n` non-empty lines of a text file, reading only its end."""
    with path.open("rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(max(0, size - block))
        data = f.read().decode("utf-8", "replace")
    lines = [line for line in data.splitlines() if line.strip()]
    return lines[-n:]


def expand(p: str | None) -> Path | None:
    return Path(os.path.expanduser(p)) if p else None


def load_config(path: Path | None) -> dict:
    path = path or DEFAULT_CONFIG
    if path.is_file():
        return tomllib.loads(path.read_text())
    return {}


# --- processes ------------------------------------------------------------------------------


def process_table() -> list[tuple[int, str]]:
    """(pid, command line) of every process, from /proc."""
    out = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            raw = (entry / "cmdline").read_bytes()
        except OSError:
            continue
        if raw:
            out.append((int(entry.name), raw.replace(b"\0", b" ").decode("utf-8", "replace")))
    return out


def pid_alive(pid: int, procs: dict[int, str], needle: str = "ucmd_study") -> bool:
    return pid in procs and needle in procs[pid]


# --- studies --------------------------------------------------------------------------------


def run_steps(run_toml: Path) -> int | None:
    try:
        return int(tomllib.loads(run_toml.read_text())["run"]["steps"])
    except (OSError, KeyError, ValueError, tomllib.TOMLDecodeError):
        return None


def last_thermo_row(thermo: Path) -> tuple[int, float] | None:
    """(step, time_ps) of the last complete row of a thermo.tsv."""
    try:
        for line in reversed(tail_lines(thermo, 3)):
            if line.startswith("#"):
                continue
            cols = line.split()
            if len(cols) >= 2:
                return int(cols[0]), float(cols[1])
    except (OSError, ValueError):
        return None
    return None


def study_runs(study: Path, errors: list[str]) -> list[dict]:
    """The runs of a study in plan order, with their current state read from status.json."""
    plan: list[str] = []
    try:
        plan = [r["id"] for r in read_json(study / "index.json").get("runs", [])]
    except (OSError, ValueError, KeyError):
        pass
    found: dict[str, dict] = {}
    for status in sorted((study / "runs").glob("*/*/status.json")):
        try:
            doc = read_json(status)
        except (OSError, ValueError) as exc:
            errors.append(f"{status.relative_to(study.parent)}: {exc}")
            continue
        rid = doc.get("id") or f"{status.parent.parent.name}/{status.parent.name}"
        found[rid] = {"id": rid, "state": doc.get("state", "unknown"), "dir": status.parent}
    runs = []
    for rid in plan:
        runs.append(found.pop(rid, {"id": rid, "state": "pending", "dir": None}))
    runs.extend(found.values())  # runs that are not (yet) in the index
    return runs


def inspect_studies(studies_dir: Path, procs: dict[int, str], errors: list[str]) -> list[dict]:
    out = []
    for d in sorted(p for p in studies_dir.glob("*") if (p / "study.toml").is_file()):
        try:
            doc = tomllib.loads((d / "study.toml").read_text())
        except (OSError, tomllib.TOMLDecodeError) as exc:
            errors.append(f"{d.name}/study.toml: {exc}")
            continue
        runs = study_runs(d, errors)
        driver = None
        lock = d / "driver.pid"
        try:
            pid = int(lock.read_text().strip())
            if pid_alive(pid, procs):
                driver = pid
        except (OSError, ValueError):
            pass
        counts = collections.Counter(r["state"] for r in runs)
        out.append(
            {
                "name": d.name,
                "path": d,
                "question": doc.get("study", {}).get("question", ""),
                "counts": dict(counts),
                "total": len(runs),
                "driver_pid": driver,
                "runs": runs,
            }
        )
    return out


class History:
    """Progress samples of the running runs, for the ETA (kept in memory while serving)."""

    def __init__(self) -> None:
        self.samples: dict[str, collections.deque] = collections.defaultdict(collections.deque)

    def rate_ps_per_s(self, key: str, t_s: float, ps: float) -> float | None:
        q = self.samples[key]
        if q and ps < q[-1][1]:  # restarted from an earlier checkpoint
            q.clear()
        q.append((t_s, ps))
        while q and t_s - q[0][0] > HISTORY_S:
            q.popleft()
        t0, ps0 = q[0]
        if t_s - t0 < MIN_HISTORY_S or ps <= ps0:
            return None
        return (ps - ps0) / (t_s - t0)


def running_runs(
    studies: list[dict], history: History, t_s: float, errors: list[str]
) -> list[dict]:
    out = []
    for s in studies:
        for r in s["runs"]:
            if r["state"] != "running" or r["dir"] is None:
                continue
            d: Path = r["dir"]
            steps = run_steps(d / "run.toml")
            row = last_thermo_row(d / "out" / "thermo.tsv")
            entry = {
                "study": s["name"],
                "run": r["id"],
                "driver_pid": s["driver_pid"],
                "orphan": s["driver_pid"] is None,
                "step": row[0] if row else None,
                "steps": steps,
                "time_ps": row[1] if row else None,
                "fraction": (row[0] / steps) if row and steps else None,
                "eta_s": None,
                "ns_per_day": None,
            }
            if row and steps and not entry["orphan"]:
                rate = history.rate_ps_per_s(f"{s['name']}/{r['id']}", t_s, row[1])
                if rate:
                    step_ps = row[1] / row[0] if row[0] else None
                    entry["ns_per_day"] = rate * 86.4
                    if step_ps:
                        entry["eta_s"] = (steps - row[0]) * step_ps / rate
            out.append(entry)
    return out


# --- resources ------------------------------------------------------------------------------


def telemetry(path: Path | None, errors: list[str]) -> dict | None:
    if path is None:
        return None
    try:
        with path.open() as f:
            header = f.readline().rstrip("\n").split("\t")
        last = tail_lines(path, 1)
        if not last:
            return None
        values = last[0].split("\t")
        row = dict(zip(header, values, strict=False))
        stamp = datetime.strptime(row["time_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        out = {"age_s": (datetime.now(UTC) - stamp).total_seconds()}
        for key in ("edge_C", "junction_C", "power_W", "cap_W", "busy_pct", "sclk_MHz"):
            if key in row:
                out[key] = float(row[key])
        return out
    except (OSError, KeyError, ValueError) as exc:
        errors.append(f"telemetry {path}: {exc}")
        return None


def docker_holders(image_part: str, errors: list[str]) -> list[dict] | None:
    try:
        res = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Image}}\t{{.RunningFor}}"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        errors.append(f"docker ps: {exc}")
        return None
    if res.returncode != 0:
        errors.append(f"docker ps: exit {res.returncode}")
        return None
    holders = []
    for line in res.stdout.splitlines():
        name, _, rest = line.partition("\t")
        image, _, age = rest.partition("\t")
        if image_part in image:
            holders.append({"name": name, "image": image, "running_for": age})
    return holders


def gpu_resource(cfg: dict, procs: list[tuple[int, str]], errors: list[str]) -> dict:
    tele = telemetry(expand(cfg.get("telemetry")), errors)
    holders = docker_holders(cfg.get("container_image", "ucmd-openmm"), errors)
    pause = cfg.get("pause_process_regex")
    paused_by = None
    if pause:
        rx = re.compile(pause)
        for pid, cmd in procs:
            if rx.search(cmd):
                paused_by = cmd.split()[0].rsplit("/", 1)[-1]
                break
    if paused_by:
        state, detail = "paused", f"paused: {paused_by} is running"
    elif holders is None:
        state, detail = "unknown", "docker not readable"
    elif len(holders) > 1:
        state, detail = "busy", f"{len(holders)} containers on the GPU (one job at a time!)"
    elif holders:
        state, detail = "busy", holders[0]["name"]
    else:
        state, detail = "idle", ""
    return {
        "name": cfg.get("name", "gpu0"),
        "kind": "gpu",
        "state": state,
        "detail": detail,
        "telemetry": tele,
        "holders": holders or [],
    }


def cpu_resource() -> dict:
    load = os.getloadavg()
    n = os.cpu_count() or 1
    return {
        "name": "cpu",
        "kind": "cpu",
        "state": "busy" if load[0] > 0.75 * n else "idle",
        "detail": f"load {load[0]:.1f} of {n} cores",
        "telemetry": {"load1": load[0], "load5": load[1], "cores": n},
        "holders": [],
    }


# --- queue scripts ----------------------------------------------------------------------------


def last_wait_age_s(log_lines: list[str], number: int, within_s: float = 300.0) -> float | None:
    """Age of the last "queue N waits" line of the resume log if it is recent, else None."""
    for line in reversed(log_lines):
        if f"queue {number} waits" in line:
            try:
                stamp = datetime.strptime(line.split()[0], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
            except (ValueError, IndexError):
                return None
            age = (datetime.now(UTC) - stamp).total_seconds()
            return age if age <= within_s else None
    return None


def queue_scripts(cfg: dict, procs: list[tuple[int, str]], errors: list[str]) -> list[dict]:
    """Live hand-written queue scripts (`*-queue<N>.sh`), until the scheduler of step 2 exists."""
    folder = expand(cfg.get("dir"))
    if folder is None:
        return []
    log_path = expand(cfg.get("log"))
    log_lines: list[str] = []
    if log_path and log_path.is_file():
        try:
            log_lines = log_path.read_text(errors="replace").splitlines()[-400:]
        except OSError as exc:
            errors.append(f"{log_path}: {exc}")
    out = []
    seen = set()
    for pid, cmd in procs:
        m = re.search(r"((?:gpu|cpu)-queue(\d*))\.sh", cmd)
        if not m or "bash" not in cmd.split()[0] or m.group(1) in seen:
            continue
        seen.add(m.group(1))
        number = int(m.group(2)) if m.group(2) else 0
        script = folder / f"{m.group(1)}.sh"
        description, studies = "", []
        try:
            text = script.read_text()
            comments = [
                ln.lstrip("# ").strip() for ln in text.splitlines()[:4] if ln.startswith("#")
            ]
            description = " ".join(c for c in comments if not c.startswith("!"))[:300]
            studies = sorted(set(re.findall(r"studies/([\w.\-]+)", text)))
        except OSError as exc:
            errors.append(f"{script}: {exc}")
        waiting = last_wait_age_s(log_lines, number) is not None
        out.append(
            {
                "name": m.group(1),
                "number": number,
                "pid": pid,
                "state": "waiting" if waiting else "active",
                "description": description,
                "studies": studies,
            }
        )
    return sorted(out, key=lambda q: q["number"])


# --- next -------------------------------------------------------------------------------------


def build_next(studies: list[dict], queues: list[dict], limit: int = 12) -> list[dict]:
    by_name = {s["name"]: s for s in studies}
    out: list[dict] = []
    taken: set[tuple[str, str]] = set()

    def add(study: dict, why: str) -> None:
        for r in study["runs"]:
            if (
                r["state"] in ("pending", "stopped", "failed")
                and (study["name"], r["id"]) not in taken
            ):
                taken.add((study["name"], r["id"]))
                out.append(
                    {"study": study["name"], "run": r["id"], "state": r["state"], "why": why}
                )

    for s in studies:
        if s["driver_pid"]:
            add(s, "next in the running study")
    for q in queues:
        for n in q["studies"]:
            if n in by_name and not by_name[n]["driver_pid"]:
                add(by_name[n], f"queued in {q['name']} ({q['state']})")
    for i, item in enumerate(out, 1):
        item["rank"] = i
    return out[:limit]


# --- tasks ------------------------------------------------------------------------------------

TASK_STATES = ("open", "claimed", "blocked", "done")


def read_tasks(path: Path, errors: list[str]) -> list[dict]:
    """The tasks of `path` (docs/tasks.toml) for people and agents; nothing here starts one.

    An open task with an unfinished `after` is shown as "waiting". A missing file means no tasks;
    a faulty file or entry goes into `errors` and is not shown as if it were fine."""
    if not path.is_file():
        return []
    try:
        raw = tomllib.loads(path.read_text()).get("task", [])
        if not isinstance(raw, list) or not all(isinstance(t, dict) for t in raw):
            raise ValueError("[[task]] entries expected")
    except (OSError, ValueError) as exc:
        errors.append(f"{path.name}: {exc}")
        return []
    tasks, seen = [], {}
    for t in raw:
        tid, state = t.get("id"), t.get("state")
        if not tid or tid in seen or state not in TASK_STATES:
            errors.append(f"{path.name}: task {tid!r}: duplicate or missing id, or state {state!r}")
            continue
        seen[tid] = state
        tasks.append(dict(t))
    for t in tasks:
        unknown = [a for a in t.get("after", []) if a not in seen]
        if unknown:
            errors.append(f"{path.name}: task {t['id']}: unknown after {unknown}")
        if t["state"] == "open" and any(seen.get(a) != "done" for a in t.get("after", [])):
            t["state"] = "waiting"
    order = {"claimed": 0, "open": 1, "waiting": 2, "blocked": 3, "done": 4}
    return sorted(tasks, key=lambda t: (order[t["state"]], t.get("priority", 9), t["id"]))


# --- state ------------------------------------------------------------------------------------


class Collector:
    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg
        self.history = History()
        node = cfg.get("node", {})
        self.node = node.get("name", os.uname().nodename)
        sd = node.get("studies_dir")
        self.studies_dir = (expand(sd) if sd else REPO / "studies").resolve()
        tf = node.get("tasks_file")
        self.tasks_file = expand(tf) if tf else REPO / "docs" / "tasks.toml"

    def collect(self) -> dict:
        errors: list[str] = []
        t_s = time.time()
        proc_list = process_table()
        procs = dict(proc_list)
        studies = inspect_studies(self.studies_dir, procs, errors)
        running = running_runs(studies, self.history, t_s, errors)
        queues = queue_scripts(self.cfg.get("queue_scripts", {}), proc_list, errors)
        scheduled: dict[str, list[str]] = collections.defaultdict(list)
        for q in queues:
            for n in q["studies"]:
                scheduled[n].append(q["name"])
        for s in studies:
            s["scheduled_by"] = scheduled.get(s["name"], [])
            open_runs = sum(s["counts"].get(k, 0) for k in OPEN_STATES)
            s["unscheduled"] = bool(open_runs) and not s["driver_pid"] and not s["scheduled_by"]
        resources = [gpu_resource(g, proc_list, errors) for g in self.cfg.get("gpu", [{}])]
        resources.append(cpu_resource())
        events: list[str] = []
        log = expand(self.cfg.get("queue_scripts", {}).get("log"))
        if log and log.is_file():
            try:
                events = tail_lines(log, 14)
            except OSError as exc:
                errors.append(f"{log}: {exc}")
        return {
            "schema": SCHEMA,
            "node": self.node,
            "time": now_iso(),
            "resources": resources,
            "running": running,
            "queues": queues,
            "next": build_next(studies, queues),
            "tasks": read_tasks(self.tasks_file, errors),
            "studies": [{k: v for k, v in s.items() if k not in ("path", "runs")} for s in studies],
            "events": events,
            "errors": errors,
        }


def fetch_remote(remote: dict) -> dict:
    try:
        with urllib.request.urlopen(remote["url"].rstrip("/") + "/api/state", timeout=4) as r:
            doc = json.load(r)
        doc["reachable"] = True
    except (OSError, ValueError) as exc:
        doc = {"node": remote.get("name", remote["url"]), "reachable": False, "error": str(exc)}
    doc.setdefault("node", remote.get("name", remote["url"]))
    return doc


class Cache:
    """Collects in the background; requests only read the last result."""

    def __init__(
        self,
        collector: Collector,
        remotes: list[dict],
        period_s: float,
        spool: Spool | None = None,
        registry: Registry | None = None,
    ) -> None:
        self.collector, self.remotes, self.period_s = collector, remotes, period_s
        self.spool, self.registry = spool, registry or Registry()
        self.lock = threading.Lock()
        self.doc: dict = {"schema": SCHEMA, "node": collector.node, "starting": True}
        self.remote_docs: list[dict] = []

    def refresh(self) -> None:
        try:
            doc = self.collector.collect()
        except Exception as exc:  # noqa: BLE001  # the page must show the fault, not die
            doc = {
                "schema": SCHEMA,
                "node": self.collector.node,
                "time": now_iso(),
                "errors": [f"collector failed: {exc!r}"],
            }
        if self.spool is not None:
            try:
                self.spool.requeue_stale()
                jobs = self.spool.jobs()
            except (OSError, ValueError) as exc:
                jobs = []
                doc.setdefault("errors", []).append(f"job spool: {exc}")
            finished = [j for j in jobs if j["state"] in FINISHED][-15:]
            doc["jobs"] = [j for j in jobs if j["state"] not in FINISHED] + finished
            doc["workers"] = self.registry.snapshot(self.spool)
            holders = {
                j["study"]: j["claimed_by"] for j in jobs if j["state"] in ACTIVE and j["study"]
            }
            for r in doc.get("running", []):
                if r.get("orphan") and r["study"] in holders:
                    r["orphan"], r["worker"] = False, holders[r["study"]]  # a driver on a worker
        remote_docs = [fetch_remote(r) for r in self.remotes]
        with self.lock:
            self.doc, self.remote_docs = doc, remote_docs

    def loop(self) -> None:
        while True:
            self.refresh()
            time.sleep(self.period_s)

    def snapshot(self) -> dict:
        with self.lock:
            return {**self.doc, "remotes": self.remote_docs}


# --- workers and clients ----------------------------------------------------------------------


def study_progress(study: Path) -> dict | None:
    """The run of `study` that is running, with its step; for the worker's heartbeat."""
    for status in sorted((study / "runs").glob("*/*/status.json")):
        try:
            if read_json(status).get("state") != "running":
                continue
        except (OSError, ValueError):
            continue
        d = status.parent
        row = last_thermo_row(d / "out" / "thermo.tsv")
        return {
            "run": f"{d.parent.name}/{d.name}",
            "step": row[0] if row else None,
            "steps": run_steps(d / "run.toml"),
            "time_ps": row[1] if row else None,
        }
    return None


def make_guard(wcfg: dict, cfg: dict):
    """Before taking a job: is somebody else on the resource? (None = free)"""

    def guard() -> str | None:
        image = wcfg.get("container_image")
        if image:
            holders = docker_holders(image, [])
            if holders:
                return f"{len(holders)} container(s) of {image} are running"
        if wcfg.get("wait_for_queue_scripts"):
            live = queue_scripts(cfg.get("queue_scripts", {}), process_table(), [])
            if live:
                return "queue script(s) alive: " + ", ".join(q["name"] for q in live)
        return None

    return guard


def make_pause(wcfg: dict):
    rx = re.compile(wcfg["pause_process_regex"]) if wcfg.get("pause_process_regex") else None

    def paused() -> str | None:
        if rx is None:
            return None
        for _, cmd in process_table():
            if rx.search(cmd):
                return "paused: " + cmd.split()[0].rsplit("/", 1)[-1] + " is running"
        return None

    return paused


def token_of(cfg: dict, entry: dict | None = None) -> str | None:
    return (
        os.environ.get("UCMD_QUEUE_TOKEN")
        or (entry or {}).get("token")
        or cfg.get("server", {}).get("token")
        or cfg.get("client", {}).get("token")
    )


def spool_of(cfg: dict) -> Spool:
    root = cfg.get("server", {}).get("spool")
    return Spool(expand(root) if root else REPO / "queue")


def cmd_work(cfg: dict, name: str | None) -> int:
    entries = cfg.get("worker", [])
    entry = next((w for w in entries if name in (None, w.get("name"))), None)
    if entry is None:
        print(f"no [[worker]] {name or ''} in the config", file=sys.stderr)
        return 2
    token = token_of(cfg, entry)
    if not token:
        print("no token: set [server] token (or UCMD_QUEUE_TOKEN)", file=sys.stderr)
        return 2
    port = cfg.get("server", {}).get("port", 8765)
    api = Api(entry.get("server", f"http://127.0.0.1:{port}"), token)
    sd = entry.get("studies_dir") or cfg.get("node", {}).get("studies_dir")
    studies_dir = expand(sd) if sd else REPO / "studies"
    logs = (spool_of(cfg).root / "logs") if not entry.get("server") else REPO / "queue" / "logs"
    worker = Worker(
        entry,
        api,
        REPO,
        studies_dir.resolve(),
        logs,
        make_guard(entry, cfg),
        make_pause(entry),
        study_progress,
        log=lambda m: print(f"{now_iso()}  {m}", flush=True),
    )
    worker.serve()
    return 0


def backend(cfg: dict, args) -> object:
    """Where agents put jobs: this machine's spool, or a server over HTTP."""
    url = args.server or cfg.get("client", {}).get("server")
    if not url:
        return LocalBackend(spool_of(cfg))
    token = args.token or token_of(cfg)
    if not token:
        raise SystemExit("no token for the server: [client] token, --token or UCMD_QUEUE_TOKEN")
    return HttpBackend(Api(url, token))


class LocalBackend:
    def __init__(self, spool: Spool) -> None:
        self.spool = spool

    def submit(self, **kw) -> dict:
        return self.spool.submit(**kw)

    def jobs(self) -> list[dict]:
        return self.spool.jobs()

    def cancel(self, job_id: str) -> dict:
        return self.spool.cancel(job_id)

    def priority(self, job_id: str, priority: int) -> dict:
        return self.spool.set_priority(job_id, priority)


class HttpBackend:
    def __init__(self, api: Api) -> None:
        self.api = api

    def submit(self, **kw) -> dict:
        return self.api.post("/api/jobs", kw)

    def jobs(self) -> list[dict]:
        return self.api.get("/api/jobs")["jobs"]

    def cancel(self, job_id: str) -> dict:
        return self.api.post(f"/api/jobs/{job_id}/cancel", {})

    def priority(self, job_id: str, priority: int) -> dict:
        return self.api.post(f"/api/jobs/{job_id}/priority", {"priority": priority})


def job_line(j: dict) -> str:
    what = (
        j["study"] + (" " + ",".join(j["runs"]) if j.get("runs") else "")
        if j["study"]
        else (" ".join(j["argv"] or []))
    )
    who = f" on {j['claimed_by']}" if j.get("claimed_by") else ""
    return f"{j['id']}  {j['state']:9s} p{j['priority']:<3d} {j['needs']:14s} {what[:70]}{who}"


def cmd_client(cfg: dict, args) -> int:
    be = backend(cfg, args)
    who = (
        args.as_
        or os.environ.get("UCMD_QUEUE_AS")
        or f"{os.environ.get('USER', '?')}@{os.uname().nodename}"
    )
    try:
        if args.command == "submit":
            kw = {
                "kind": args.kind,
                "needs": args.needs,
                "title": args.title or "",
                "priority": args.priority,
                "first": args.first,
                "after": args.after or [],
                "submitted_by": who,
                "note": args.note or "",
            }
            if args.kind == "study":
                kw.update(study=args.study, runs=args.runs)
            else:
                kw.update(argv=args.argv[1:] if args.argv[:1] == ["--"] else args.argv)
            print(job_line(be.submit(**kw)))
        elif args.command == "jobs":
            jobs = be.jobs()
            if not args.all:
                jobs = [j for j in jobs if j["state"] not in FINISHED]
            for j in sorted(
                jobs, key=lambda j: (j["state"] != "running", -j["priority"], j["submitted"])
            ):
                print(job_line(j))
            if not jobs:
                print("no jobs" if args.all else "no open jobs (--all shows finished ones)")
        elif args.command == "cancel":
            print(job_line(be.cancel(args.job)))
        elif args.command == "priority":
            print(job_line(be.priority(args.job, args.value)))
    except (JobError, ServerError) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 1
    return 0


def serve(cfg: dict, args) -> int:
    server_cfg = cfg.get("server", {})
    bind = args.bind or server_cfg.get("bind", "127.0.0.1")
    port = args.port or server_cfg.get("port", 8765)
    token = token_of({"server": server_cfg})
    if bind not in ("127.0.0.1", "localhost", "::1") and not token:
        print(
            "refusing to listen beyond this machine without a token ([server] token)",
            file=sys.stderr,
        )
        return 2
    collector = Collector(cfg)
    spool, registry = spool_of(cfg), Registry()
    cache = Cache(collector, cfg.get("remote", []), args.period, spool, registry)
    cache.refresh()
    threading.Thread(target=cache.loop, daemon=True).start()
    page = (HERE / "dashboard.html").read_bytes()
    server = ThreadingHTTPServer((bind, port), make_handler(cache, page, spool, registry, token))
    mode = "token set" if token else "no token: read-only"
    print(f"queue server on http://{bind}:{port}  ({mode}; Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--config", type=Path, default=None)
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("serve", help="dashboard and job API")
    p.add_argument("--port", type=int, default=None)
    p.add_argument("--bind", default=None, help="address; default 127.0.0.1 (LAN needs a token)")
    p.add_argument("--period", type=float, default=10.0, help="seconds between collections")
    sub.add_parser("state", help="print the dashboard state once")
    p = sub.add_parser("work", help="run as a worker: take jobs from the server")
    p.add_argument("--worker", default=None, help="which [[worker]] of the config")

    def client(p: argparse.ArgumentParser) -> None:
        p.add_argument("--server", default=None, help="URL; default: this machine's spool")
        p.add_argument("--token", default=None)

    p = sub.add_parser("submit", help="queue a job")
    client(p)
    kinds = p.add_subparsers(dest="kind", required=True)
    for kind in ("study", "command"):
        k = kinds.add_parser(kind)
        if kind == "study":
            k.add_argument("study", help="folder name under studies/")
            k.add_argument("--runs", nargs="+", metavar="ID", help="only these runs")
        else:
            k.add_argument("argv", nargs=argparse.REMAINDER, help="-- COMMAND ARGS...")
        k.add_argument("--needs", required=True, help="resource tag: gpu-hip-mixed, cpu, ...")
        k.add_argument("--priority", type=int, default=0, help="larger goes first (default 0)")
        k.add_argument("--first", action="store_true", help="before everything queued")
        k.add_argument("--after", nargs="+", metavar="JOB", help="start only after these are done")
        k.add_argument("--title")
        k.add_argument("--note")
        k.add_argument("--as", dest="as_", help="who submits (a session name)")
    p = sub.add_parser("jobs", help="list jobs")
    client(p)
    p.add_argument("--all", action="store_true")
    p = sub.add_parser("cancel", help="cancel a job (a running one stops gracefully)")
    client(p)
    p.add_argument("job")
    p = sub.add_parser("priority", help="change the priority of a queued job")
    client(p)
    p.add_argument("job")
    p.add_argument("value", type=int)
    args = ap.parse_args(argv)
    if args.command in ("jobs", "cancel", "priority"):
        args.as_ = None
    cfg = load_config(args.config)
    if args.command == "state":
        print(json.dumps(Collector(cfg).collect(), indent=2))
        return 0
    if args.command == "serve":
        return serve(cfg, args)
    if args.command == "work":
        return cmd_work(cfg, args.worker)
    return cmd_client(cfg, args)


if __name__ == "__main__":
    sys.exit(main())
