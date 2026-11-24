"""Dashboard of this machine's compute queue: what runs, what waits, what comes next.

    python3 tools/queue/ucmd_queue.py serve [--port 8765] [--config FILE]
    python3 tools/queue/ucmd_queue.py state [--config FILE]       # the JSON once

Read-only (docs/design/queue.md, step 1): it reads status.json / thermo.tsv of the studies, the
driver locks, a GPU telemetry file, the process list, `docker ps` and the queue scripts' log, and
changes nothing. Serves on 127.0.0.1 only. Machine-specific settings are in
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
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

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


# --- state ------------------------------------------------------------------------------------


class Collector:
    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg
        self.history = History()
        node = cfg.get("node", {})
        self.node = node.get("name", os.uname().nodename)
        sd = node.get("studies_dir")
        self.studies_dir = (expand(sd) if sd else REPO / "studies").resolve()

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

    def __init__(self, collector: Collector, remotes: list[dict], period_s: float) -> None:
        self.collector, self.remotes, self.period_s = collector, remotes, period_s
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


def make_handler(cache: Cache, page: bytes):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            path = self.path.split("?", 1)[0]
            if path in ("/", "/index.html"):
                self._send(200, page, "text/html; charset=utf-8")
            elif path == "/api/state":
                self._send(200, json.dumps(cache.snapshot()).encode(), "application/json")
            else:
                self._send(404, b"not found", "text/plain")

        def _refuse(self) -> None:
            self._send(405, b"read-only", "text/plain")

        do_POST = do_PUT = do_DELETE = do_PATCH = _refuse

        def log_message(self, fmt: str, *args) -> None:  # quiet
            pass

    return Handler


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("command", choices=["serve", "state"])
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--config", type=Path, default=None)
    ap.add_argument("--period", type=float, default=10.0, help="seconds between collections")
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    collector = Collector(cfg)
    if args.command == "state":
        print(json.dumps(collector.collect(), indent=2))
        return 0
    cache = Cache(collector, cfg.get("remote", []), args.period)
    cache.refresh()
    threading.Thread(target=cache.loop, daemon=True).start()
    page = (HERE / "dashboard.html").read_bytes()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(cache, page))
    print(f"queue dashboard on http://127.0.0.1:{args.port}  (read-only, Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
