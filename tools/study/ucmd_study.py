"""Run and index a simulation study: many systems × many conditions (ADR 0011).

    python3 tools/study/ucmd_study.py plan   STUDY_DIR      # the runs, their order, the cost
    python3 tools/study/ucmd_study.py run    STUDY_DIR [--ucmd PATH] [--max-runs N] [--nice N]
                                             [--stall-minutes M] [--retry-failed]
    python3 tools/study/ucmd_study.py status STUDY_DIR      # rebuild INDEX.md, views/, CATALOG.md
    python3 tools/study/ucmd_study.py stop   STUDY_DIR      # graceful: the engine checkpoints

A study is a folder with a `study.toml` (the plan). The driver builds every system with
`ucmd-build`, minimizes it once with `ucmd minimize`, and runs every condition with `ucmd run`.
It is a thin orchestrator: it calls the components' command-line programs and reads only
spec'd files (run.toml, the thermo table). It is resumable: finished runs are skipped, stopped
runs continue from their checkpoint (`ucmd run --restart`).

Standard library only (Python ≥ 3.11).
"""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import glob
import hashlib
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import tomllib
import zlib
from dataclasses import dataclass, field
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]  # UnitcellMD/
STUDIES = WORKSPACE / "studies"
ZERO_CELSIUS_K = 273.15  # definition of the Celsius scale
GRAM_PER_AMU = 1.66053906660e-24  # CODATA 2018 atomic mass constant
CM3_PER_NM3 = 1e-21
STOPPED = (130, 143)  # the engine stopped gracefully on SIGINT / SIGTERM
RESUMABLE = ("running", "stopped", "stalled")  # continue from the checkpoint, if there is one
KILL_GRACE_S = 60.0  # after SIGTERM, how long a stalled engine gets to exit before SIGKILL


# -- the plan -----------------------------------------------------------------------------------


@dataclass(frozen=True)
class System:
    name: str  # recipe or package stem, e.g. "ec-emc_3-7w_1.0M"
    recipe: Path  # the recipe, or for a ready package (`[systems] packages`) the package
    labels: dict[str, str]  # from [systems] label, e.g. mixture, concentration_M
    ready: bool = False  # a ready package: no build, no minimization


@dataclass(frozen=True)
class Task:
    system: System
    temperature_C: float

    @property
    def T(self) -> str:  # folder label, e.g. "T-10C", "T20C"
        return f"T{self.temperature_C:g}C"

    @property
    def temperature_K(self) -> float:
        return round(self.temperature_C + ZERO_CELSIUS_K, 6)

    @property
    def id(self) -> str:
        return f"{self.system.name}/{self.T}"


@dataclass
class Study:
    dir: Path
    doc: dict
    systems: list[System] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)

    @property
    def name(self) -> str:
        return self.dir.name


def load_study(study_dir: Path) -> Study:
    study_dir = study_dir.resolve()
    with (study_dir / "study.toml").open("rb") as fh:
        doc = tomllib.load(fh)
    study = Study(study_dir, doc)
    # systems from recipes (built and minimized here) or ready packages (e.g. the end of an
    # equilibration, made with tools/study/package_from_run.py)
    ready = "packages" in doc["systems"]
    patterns = doc["systems"]["packages" if ready else "recipes"]
    patterns = [patterns] if isinstance(patterns, str) else patterns
    label = re.compile(doc["systems"].get("label", r"^(?P<system>.+)$"))
    paths = sorted({Path(p) for pat in patterns for p in glob.glob(str(study_dir / pat))})
    if not paths:
        raise SystemExit(f"{study_dir}: no systems match {patterns!r}")
    for path in paths:
        m = label.match(path.stem)
        if m is None:
            raise SystemExit(f"{path.name}: does not match [systems] label {label.pattern!r}")
        study.systems.append(System(path.stem, path, m.groupdict(), ready))
    temperatures = doc["scan"]["temperature_C"]
    tasks = [Task(s, float(t)) for s in study.systems for t in temperatures]
    priority = doc["scan"].get("priority", {})

    def rank(task: Task) -> tuple:
        key = []
        for name, order in priority.items():
            value = task.system.labels.get(name)
            key.append(order.index(value) if value in order else len(order))
        return (*key, task.system.name, task.temperature_C)

    study.tasks = sorted(tasks, key=rank)
    return study


# -- TOML output (stdlib has a reader only) -----------------------------------------------------


def _toml_value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if not math.isfinite(v):
            raise ValueError(f"not a finite number: {v}")
        text = repr(v)
        return text if any(c in text for c in ".en") else text + ".0"
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "[" + ", ".join(_toml_value(x) for x in v) + "]"
    raise TypeError(f"cannot write {type(v).__name__} to TOML")


def to_toml(doc: dict, prefix: str = "") -> str:
    """Nested dicts of scalars and lists; lists of dicts become arrays of tables."""
    lines, tables, arrays = [], [], []
    for k, v in doc.items():
        if isinstance(v, dict):
            tables.append((k, v))
        elif isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
            arrays.append((k, v))
        else:
            lines.append(f"{k} = {_toml_value(v)}")
    out = "\n".join(lines) + ("\n" if lines else "")
    for k, v in tables:
        name = f"{prefix}{k}"
        out += f"\n[{name}]\n" + to_toml(v, name + ".")
    for k, items in arrays:
        for item in items:
            out += f"\n[[{prefix}{k}]]\n" + to_toml(item, f"{prefix}{k}.")
    return out


# -- files of one run ---------------------------------------------------------------------------


def system_dir(study: Study, system: System) -> Path:
    return study.dir / "systems" / system.name


def run_dir(study: Study, task: Task) -> Path:
    return study.dir / "runs" / task.system.name / task.T


def seed_of(study: Study, task: Task) -> int:
    """A seed that depends only on the study seed and the run id, not on the run order."""
    return int(study.doc["protocol"]["seed"]) + zlib.crc32(task.id.encode()) % 1_000_000


def minimize_toml(study: Study, system: System) -> str:
    doc = copy.deepcopy(study.doc["minimize_template"])
    doc = {"spec_version": doc.pop("spec_version", "0.1.0"), "system": "built.ucsys", **doc}
    doc["title"] = f"{study.name}: minimization of {system.name}"
    return to_toml(doc)


def run_toml(study: Study, task: Task) -> str:
    """The run_template of study.toml with system, title, seed and temperatures filled in."""
    doc = copy.deepcopy(study.doc["run_template"])
    system = os.path.relpath(
        system_dir(study, task.system) / "minimized.ucsys", run_dir(study, task)
    )
    doc = {"spec_version": doc.pop("spec_version", "0.1.0"), "system": system, **doc}
    doc["title"] = f"{study.name}: {task.system.name} at {task.temperature_C:g} °C"
    doc["run"]["seed"] = seed_of(study, task)
    doc.setdefault("velocities", {})["temperature_K"] = task.temperature_K
    doc["thermostat"]["temperature_K"] = task.temperature_K
    return to_toml(doc)


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def write_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def now() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# -- thermo summary (bookkeeping for the index; interpretation belongs to ucmd-analysis) -------


def read_thermo(path: Path) -> tuple[list[str], list[list[float]]]:
    names, rows = [], []
    try:
        text = path.read_text()
    except OSError:
        return names, rows
    for line in text.splitlines():
        if line.startswith("#"):
            names = line.lstrip("# ").split("\t")
        elif names:
            parts = line.split("\t")
            if len(parts) == len(names):
                try:
                    rows.append([float(p) for p in parts])
                except ValueError:
                    pass
    return names, rows


def summarize(path: Path, from_fraction: float = 0.5) -> dict:
    """Mean and standard deviation of the main columns over the last half of the run."""
    names, rows = read_thermo(path)
    if not rows:
        return {}
    t = [r[names.index("time_ps")] for r in rows]
    start = t[-1] * from_fraction
    window = [r for r in rows if r[names.index("time_ps")] >= start]
    out = {"last_time_ps": t[-1], "window_ps": [start, t[-1]], "rows": len(window)}
    for col in ("temperature_K", "pressure_bar", "potential_kjmol", "total_kjmol", "volume_nm3"):
        if col in names:
            # a backend may report a column only on some rows (OpenMM: pressure on barostat
            # steps) and writes nan on the others; average over the rows that have a value
            xs = [x for r in window if math.isfinite(x := r[names.index(col)])]
            if not xs:
                continue
            mean = sum(xs) / len(xs)
            sd = math.sqrt(sum((x - mean) ** 2 for x in xs) / max(1, len(xs) - 1))
            out[col] = {"mean": mean, "sd": sd}
    if "conserved_energy_kjmol" in names:
        h = [r[names.index("conserved_energy_kjmol")] for r in window]
        span = window[-1][names.index("time_ps")] - window[0][names.index("time_ps")]
        out["conserved_drift_kjmol_per_ps"] = (h[-1] - h[0]) / span if span > 0 else 0.0
    return out


# -- executables --------------------------------------------------------------------------------


def machine_profile() -> dict:
    """The per-machine profile of spec/run-config.md §4 (first existing file)."""
    candidates = []
    if os.environ.get("UCMD_MACHINE_PROFILE"):
        candidates.append(Path(os.environ["UCMD_MACHINE_PROFILE"]))
    if os.environ.get("XDG_CONFIG_HOME"):
        candidates.append(Path(os.environ["XDG_CONFIG_HOME"]) / "ucmd" / "machine.toml")
    candidates.append(Path.home() / ".config" / "ucmd" / "machine.toml")
    for path in candidates:
        if path.is_file():
            with path.open("rb") as fh:
                return tomllib.load(fh)
    return {}


def find_executables(ucmd: str | None) -> tuple[Path, Path]:
    exe = machine_profile().get("executables", {})
    engine = Path(ucmd or exe.get("ucmd") or WORKSPACE / "ucmd-engine/target/release/ucmd")
    builder = Path(exe.get("ucmd-build") or WORKSPACE / "ucmd-builder/.venv/bin/ucmd-build")
    for path, what in ((engine, "engine (ucmd)"), (builder, "builder (ucmd-build)")):
        if not (path.is_file() and os.access(path, os.X_OK)):
            raise SystemExit(f"{what} not found or not executable: {path}")
    version = subprocess.run(
        [engine, "--version"], check=False, capture_output=True, text=True
    ).stdout
    if not version.startswith("ucmd "):
        raise SystemExit(f"{engine} is not the UnitcellMD engine (--version: {version!r})")
    return engine, builder


def system_mass_amu(system_json: dict) -> float | None:
    """Total mass of a package from its molecule types and component counts (amu)."""
    try:
        types = system_json["molecule_types"]
        return sum(
            c["count"] * sum(a["mass_amu"] for a in types[c["molecule_type"]]["atoms"])
            for c in system_json["components"]
        )
    except (KeyError, TypeError):
        return None


def version_of(program: Path) -> str:
    result = subprocess.run([program, "--version"], check=False, capture_output=True, text=True)
    return result.stdout.strip()


# -- running ------------------------------------------------------------------------------------


class Driver:
    def __init__(
        self, study: Study, engine: Path, builder: Path, nice: int, stall_minutes: float = 0.0
    ) -> None:
        self.study, self.engine, self.builder, self.nice = study, engine, builder, nice
        self.stall_s = 60.0 * stall_minutes  # 0: no watchdog
        self.child: subprocess.Popen | None = None
        self.stop_requested = False
        self.stalled = False  # the last call was ended by the watchdog
        self.log_path = study.dir / "logs" / "driver.log"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, text: str) -> None:
        line = f"{now()}  {text}"
        print(line, flush=True)
        with self.log_path.open("a") as fh:
            fh.write(line + "\n")

    def request_stop(self, signum, _frame) -> None:
        if self.stop_requested and self.child is not None:
            self.child.kill()  # second signal: no more waiting
            return
        self.stop_requested = True
        self.log(f"signal {signum}: stopping after the engine has written its checkpoint")
        if self.child is not None and self.child.poll() is None:
            self.child.send_signal(signal.SIGTERM)

    def call(self, args: list, cwd: Path, log: Path, watch: tuple[Path, ...] = ()) -> int:
        """Run a program to its end. With `watch` and a stall time, a watchdog ends it when
        none of the watched files has changed for that long (a hung GPU, a dead container)."""
        nice = shutil.which("nice")
        if self.nice and nice:  # lower priority, so the workstation stays usable
            args = [nice, "-n", str(self.nice), *args]
        self.stalled = False
        with log.open("a") as fh:
            fh.write(f"\n{now()}  $ {' '.join(str(a) for a in args)}\n")
            fh.flush()
            self.child = subprocess.Popen(
                [str(a) for a in args],
                cwd=cwd,
                stdout=fh,
                stderr=subprocess.STDOUT,
                start_new_session=True,  # its own process group, so a stall ends the bridge too
            )
            code = self._wait(watch, time.time())
            self.child = None
        return code

    def _wait(self, watch: tuple[Path, ...], started: float) -> int:
        assert self.child is not None
        if not (watch and self.stall_s > 0):
            return self.child.wait()
        poll = max(0.05, min(30.0, self.stall_s / 4))
        while True:
            try:
                return self.child.wait(timeout=poll)
            except subprocess.TimeoutExpired:
                pass
            mtimes = [p.stat().st_mtime for p in watch if p.exists()]
            quiet = time.time() - max([started, *mtimes])
            if quiet < self.stall_s or self.stop_requested:
                continue
            self.stalled = True
            self.log(
                f"watchdog: no output for {quiet / 60:.0f} min; ending the engine "
                "(SIGTERM, then SIGKILL); if it used the GPU container, check `docker ps`"
            )
            self._signal_group(signal.SIGTERM)
            try:
                return self.child.wait(timeout=KILL_GRACE_S)
            except subprocess.TimeoutExpired:
                self._signal_group(signal.SIGKILL)
                return self.child.wait()

    def _signal_group(self, signum: int) -> None:
        assert self.child is not None
        try:
            os.killpg(self.child.pid, signum)
        except ProcessLookupError:
            pass

    # one system: build + minimize, once
    def prepare(self, system: System) -> bool:
        d = system_dir(self.study, system)
        d.mkdir(parents=True, exist_ok=True)
        status_path = d / "status.json"
        status = read_json(status_path)
        if status.get("state") == "minimized" and (d / "minimized.ucsys").is_dir():
            return True
        if status.get("state") == "failed":
            return False
        status.update(system=system.name, labels=system.labels)
        if system.ready:
            # a ready package: copied once as the run's start, without build or minimization
            target = d / "minimized.ucsys"
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(system.recipe, target)
            system_json = read_json(target / "system.json")
            status.update(
                state="minimized",
                package=os.path.relpath(system.recipe, self.study.dir),
                package_sha256=sha256(target / "system.json"),
                atoms=system_json.get("atom_count"),
                mass_amu=system_mass_amu(system_json),
            )
            write_json(status_path, status)
            self.log(f"{system.name}: ready package {status['package']}")
            return True
        if not (d / "built.ucsys").is_dir():
            shutil.copyfile(system.recipe, d / "recipe.toml")
            status.update(state="building", recipe=os.path.relpath(system.recipe, self.study.dir))
            status["recipe_sha256"] = sha256(d / "recipe.toml")
            write_json(status_path, status)
            self.log(f"build {system.name}")
            t0 = time.time()
            code = self.call(
                [self.builder, "build", "recipe.toml", "-o", "built.ucsys"], d, d / "build.log"
            )
            if code != 0:
                status.update(state="failed", reason=f"build exit {code}; see build.log")
                write_json(status_path, status)
                return False
            status.update(build_s=round(time.time() - t0, 1), builder=version_of(self.builder))
        system_json = read_json(d / "built.ucsys" / "system.json")
        status["atoms"] = system_json.get("atom_count") or status.get("atoms")
        status["mass_amu"] = system_mass_amu(system_json) or status.get("mass_amu")
        (d / "minimize.toml").write_text(minimize_toml(self.study, system))
        if (d / "minimized.ucsys").exists():
            shutil.rmtree(d / "minimized.ucsys")  # a partial one from an interrupted minimization
        status["state"] = "minimizing"
        write_json(status_path, status)
        self.log(f"minimize {system.name}")
        t0 = time.time()
        args = [self.engine, "minimize", "minimize.toml", "--out", "minimized.ucsys"]
        code = self.call(args, d, d / "minimize.log")
        if self.stop_requested and code in STOPPED + (-signal.SIGTERM,):
            status["state"] = "built"
            write_json(status_path, status)
            return False
        if code != 0:
            status.update(state="failed", reason=f"minimize exit {code}; see minimize.log")
            write_json(status_path, status)
            return False
        status.update(state="minimized", minimize_s=round(time.time() - t0, 1))
        status["engine"] = version_of(self.engine)
        write_json(status_path, status)
        return True

    def run_task(self, task: Task) -> str:
        d = run_dir(self.study, task)
        d.mkdir(parents=True, exist_ok=True)
        status_path = d / "status.json"
        status = read_json(status_path)
        text = run_toml(self.study, task)
        old = d / "run.toml"
        if old.exists() and old.read_text() != text and (d / "out").exists():
            status.update(state="failed", reason="run.toml differs from study.toml; see docs")
            write_json(status_path, status)
            return "failed"
        (d / "run.toml").write_text(text)
        check = subprocess.run(
            [self.engine, "check", "run.toml"], check=False, cwd=d, capture_output=True, text=True
        )
        if check.returncode != 0:
            status.update(state="failed", reason=f"ucmd check: {check.stdout}{check.stderr}")
            write_json(status_path, status)
            return "failed"
        args = [self.engine, "run", "run.toml"]
        checkpoint = d / "out" / "checkpoint.ucchk"
        # a failed run (only reached with --retry-failed) also continues: the checkpoint holds
        # the last good state (invariant 7), and the engine cuts its outputs back to it
        if checkpoint.is_file() and status.get("state") in (*RESUMABLE, "failed"):
            args += ["--restart", "out/checkpoint.ucchk"]
            self.log(f"continue {task.id} from its checkpoint ({status.get('state')})")
        else:
            if (d / "out").exists():
                shutil.rmtree(d / "out")
            self.log(f"run {task.id}")
        # a reason belongs to the attempt that failed; this attempt writes its own if it fails too
        status.pop("reason", None)
        status.update(
            id=task.id,
            system=task.system.name,
            labels=task.system.labels,
            temperature_C=task.temperature_C,
            temperature_K=task.temperature_K,
            seed=seed_of(self.study, task),
            state="running",
            engine=version_of(self.engine),
            started=status.get("started") or now(),
        )
        write_json(status_path, status)
        t0 = time.time()
        code = self.call(args, d, d / "run.log", watch=(d / "out" / "thermo.tsv", d / "run.log"))
        status["wall_s"] = round(status.get("wall_s", 0.0) + time.time() - t0, 1)
        status["exit"] = code
        status["summary"] = summarize(d / "out" / "thermo.tsv")
        if code == 0:
            status.update(state="done", finished=now())
        elif self.stalled:
            status.update(
                state="stalled",
                reason=f"no output for {self.stall_s / 60:g} min; ended by the watchdog",
            )
        elif code in STOPPED or (self.stop_requested and checkpoint.is_file()):
            # a stop we asked for; an engine stuck in its backend may not exit cleanly
            status["state"] = "stopped"
        else:
            status.update(state="failed", reason=f"engine exit {code}; see run.log")
        write_json(status_path, status)
        return status["state"]

    def run(self, max_runs: int | None, retry_failed: bool) -> int:
        lock = self.study.dir / "driver.pid"
        if lock.exists():
            pid = int(lock.read_text().strip() or 0)
            try:
                os.kill(pid, 0)
                raise SystemExit(f"a driver is already running for this study (pid {pid})")
            except ProcessLookupError:
                pass
        lock.write_text(f"{os.getpid()}\n")
        signal.signal(signal.SIGTERM, self.request_stop)
        signal.signal(signal.SIGINT, self.request_stop)
        self.log(f"driver start: {len(self.study.tasks)} runs; engine {version_of(self.engine)}")
        done_now = 0
        try:
            for task in self.study.tasks:
                if self.stop_requested or (max_runs is not None and done_now >= max_runs):
                    break
                state = read_json(run_dir(self.study, task) / "status.json").get("state")
                if state == "done" or (state == "failed" and not retry_failed):
                    continue
                if not self.prepare(task.system):
                    if self.stop_requested:
                        break
                    continue
                state = self.run_task(task)
                done_now += state == "done"
                self.log(f"{task.id}: {state}")
                write_index(self.study)
                if state == "stalled":
                    # a hung GPU or driver: the next runs would hang the same way
                    self.log("stopping the study after a stall; `run` again continues it")
                    break
        finally:
            write_index(self.study)
            lock.unlink(missing_ok=True)
            self.log("driver end")
        return 0


# -- the index: INDEX.md, index.json, views/, ../CATALOG.md ---------------------------------------


def collect(study: Study) -> list[dict]:
    records = []
    for task in study.tasks:
        d = run_dir(study, task)
        status = read_json(d / "status.json")
        system = read_json(system_dir(study, task.system) / "status.json")
        state = status.get("state") or (
            "system failed" if system.get("state") == "failed" else "pending"
        )
        record = {
            "id": task.id,
            "system": task.system.name,
            **task.system.labels,
            "temperature_C": task.temperature_C,
            "T": task.T,
            "state": state,
            "atoms": system.get("atoms"),
            "mass_amu": system.get("mass_amu"),
            "folder": os.path.relpath(d, study.dir),
        }
        if state == "running":
            record["summary"] = summarize(d / "out" / "thermo.tsv")
        else:
            record["summary"] = status.get("summary", {})
        for key in ("wall_s", "reason", "engine", "seed", "finished"):
            if key in status:
                record[key] = status[key]
        v = record["summary"].get("volume_nm3")
        if v and record["mass_amu"]:
            record["density_g_cm3"] = record["mass_amu"] * GRAM_PER_AMU / (v["mean"] * CM3_PER_NM3)
        records.append(record)
    return records


def folder_size(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file() and not p.is_symlink())


def human(n: float) -> str:
    for unit in ("B", "kB", "MB", "GB", "TB"):
        if n < 1000:
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1000
    return f"{n:.1f} PB"


def write_views(study: Study, records: list[dict]) -> None:
    """Symbolic links that sort the runs in other ways (views/<name>/...); only links, no data."""
    views = study.dir / "views"
    if views.exists():
        shutil.rmtree(views)
    for name, template in study.doc.get("views", {}).items():
        for r in records:
            target = study.dir / r["folder"]
            if not target.exists():
                continue
            link = views / name / template.format(**r)
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(os.path.relpath(target, link.parent))


def fmt(summary: dict, key: str, digits: int = 0) -> str:
    v = summary.get(key)
    return f"{v['mean']:.{digits}f} ± {v['sd']:.{digits}f}" if v else "–"


def write_index(study: Study) -> dict:
    records = collect(study)
    write_views(study, records)
    counts: dict[str, int] = {}
    for r in records:
        counts[r["state"]] = counts.get(r["state"], 0) + 1
    done = [r for r in records if r["state"] == "done" and r.get("wall_s")]
    known = [r["atoms"] for r in records if r["atoms"]]
    typical = sum(known) / len(known) if known else 0  # for systems not built yet
    remaining_atoms = sum(r["atoms"] or typical for r in records if r["state"] != "done")
    if done:
        s_per_atom = sum(r["wall_s"] for r in done) / sum(r["atoms"] for r in done)
        eta = f"about {remaining_atoms * s_per_atom / 3600:.0f} h left at the measured speed"
    else:
        eta = "no finished run yet to measure the speed"
    size = folder_size(study.dir)
    total = len(records)
    meta = study.doc.get("study", {})
    index = {
        "study": study.name,
        "updated": now(),
        "question": meta.get("question", ""),
        "counts": counts,
        "bytes": size,
        "runs": records,
    }
    write_json(study.dir / "index.json", index)

    temperatures = study.doc["scan"]["temperature_C"]
    grid = study.doc.get("index", {}).get("grid", "pressure")
    grid_title = "⟨ρ⟩ in g/cm³" if grid == "density" else "⟨P⟩ in bar"
    group_key = study.doc.get("index", {}).get("group_by", "system")
    row_key = study.doc.get("index", {}).get("row_by", "system")
    lines = [
        f"# {study.name} — index",
        "",
        f"Generated {index['updated']} by `tools/study/ucmd_study.py status`; do not edit.",
        "",
        f"- **Question:** {meta.get('question', '–')}",
        f"- **Progress:** {counts.get('done', 0)} of {total} runs done"
        + "".join(f", {n} {s}" for s, n in sorted(counts.items()) if s != "done")
        + f"; {eta}.",
        f"- **Data:** {human(size)} in this folder.",
        "",
        "## What is where",
        "",
        "```",
        f"{study.name}/",
        "├── study.toml          the plan: systems, conditions, protocol (edit before a run only)",
        "├── README.md           purpose, protocol and caveats (written by hand)",
        "├── INDEX.md            this file (generated)",
        "├── index.json          the same, machine-readable (generated)",
        "├── systems/<system>/   recipe.toml (copy), built.ucsys, minimize.toml, minimized.ucsys,",
        "│                       build.log, minimize.log, status.json",
        "├── runs/<system>/<T>/  run.toml, run.log, status.json,",
        "│                       out/ thermo.tsv, trajectory.h5, checkpoint.ucchk",
        "├── views/              symbolic links only: the same runs sorted differently",
    ]
    views = list(study.doc.get("views", {}).items())
    for k, (name, template) in enumerate(views):
        lines.append(f"│   {'└──' if k == len(views) - 1 else '├──'} {name}/{template}")
    lines += [
        "└── logs/driver.log     what the driver did, with times",
        "```",
        "",
        f"Open a run in the GUI: `ucmd-builder/start-gui.sh studies/{study.name}/runs/<system>/<T>`.",
        "",
        f"## {grid_title} over the second half of each run",
        "",
        "Cells show the value when a run is done, else its state.",
        "",
    ]
    groups: dict[str, list[dict]] = {}
    for r in records:
        groups.setdefault(str(r.get(group_key, r["system"])), []).append(r)
    for group, rs in groups.items():
        lines += [
            f"### {group}",
            "",
            f"| {row_key} | " + " | ".join(f"{t:g} °C" for t in temperatures) + " |",
            "|---|" + "---|" * len(temperatures),
        ]
        rows: dict[str, dict[float, dict]] = {}
        for r in rs:
            rows.setdefault(str(r.get(row_key, r["system"])), {})[r["temperature_C"]] = r
        for row, by_t in rows.items():
            cells = []
            for t in temperatures:
                r = by_t.get(float(t))
                if r is None:
                    cells.append("")
                elif r["state"] == "done" and grid == "density" and r.get("density_g_cm3"):
                    cells.append(f"{r['density_g_cm3']:.4f}")
                elif (
                    r["state"] == "done" and grid != "density" and r["summary"].get("pressure_bar")
                ):
                    cells.append(f"{r['summary']['pressure_bar']['mean']:.0f}")
                else:
                    cells.append(r["state"])
            lines.append(f"| {row} | " + " | ".join(cells) + " |")
        lines.append("")
    lines += [
        "## Every run",
        "",
        "Means ± standard deviations over the second half of the run (bookkeeping, not analysis).",
        "",
        (
            "| run | atoms | state | wall | ⟨T⟩ (K) | ⟨P⟩ (bar) | ⟨ρ⟩ (g/cm³) | ⟨E_pot⟩ (kJ/mol) |"
            " drift of H (kJ/mol/ps) |"
        ),
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in records:
        s = r["summary"]
        wall = f"{r['wall_s'] / 60:.0f} min" if r.get("wall_s") else ""
        drift = s.get("conserved_drift_kjmol_per_ps")
        state = r["state"] + (f" ({r['reason']})" if r.get("reason") else "")
        density = r.get("density_g_cm3")
        density_text = "" if density is None else f"{density:.4f}"
        lines.append(
            f"| [{r['id']}]({r['folder']}) | {r['atoms'] or ''} | {state} | {wall} | "
            f"{fmt(s, 'temperature_K', 1)} | {fmt(s, 'pressure_bar')} | {density_text} | "
            f"{fmt(s, 'potential_kjmol')} | {'' if drift is None else f'{drift:.1f}'} |"
        )
    (study.dir / "INDEX.md").write_text("\n".join(lines) + "\n")
    write_catalog()
    return index


def write_catalog() -> None:
    """studies/CATALOG.md: one line per study (generated)."""
    lines = [
        "# Studies — catalog",
        "",
        f"Generated {now()} by `tools/study/ucmd_study.py`; do not edit. Each study folder has",
        "its own README.md (purpose) and INDEX.md (contents and progress).",
        "",
        "| study | question | runs done | data |",
        "|---|---|---|---|",
    ]
    for d in sorted(p for p in STUDIES.iterdir() if (p / "study.toml").is_file()):
        index = read_json(d / "index.json")
        with (d / "study.toml").open("rb") as fh:
            meta = tomllib.load(fh).get("study", {})
        counts = index.get("counts", {})
        total = sum(counts.values())
        progress = f"{counts.get('done', 0)} / {total}" if total else "not started"
        size = human(index["bytes"]) if "bytes" in index else "–"
        lines.append(
            f"| [{d.name}]({d.name}/INDEX.md) | {meta.get('question', '')} | {progress} | {size} |"
        )
    (STUDIES / "CATALOG.md").write_text("\n".join(lines) + "\n")


# -- commands -----------------------------------------------------------------------------------


def cmd_plan(study: Study) -> int:
    atoms_per_system = {}
    for system in study.systems:
        built = system_dir(study, system) / "built.ucsys" / "system.json"
        atoms_per_system[system.name] = read_json(built).get("atom_count")
    rate = study.doc.get("estimate", {}).get("seconds_per_atom_per_run")
    total_s = 0.0
    for k, task in enumerate(study.tasks, 1):
        atoms = atoms_per_system[task.system.name]
        if rate and atoms:
            total_s += rate * atoms
        print(f"{k:4d}  {task.id:40s} {task.temperature_K:8.2f} K  seed {seed_of(study, task)}")
    print(f"{len(study.tasks)} runs of {len(study.systems)} systems")
    if total_s:
        print(f"estimate for the built systems: {total_s / 3600:.1f} h of engine time")
    return 0


def cmd_stop(study: Study) -> int:
    lock = study.dir / "driver.pid"
    if not lock.exists():
        print("no driver is running for this study")
        return 1
    pid = int(lock.read_text().strip())
    os.kill(pid, signal.SIGTERM)
    print(f"sent SIGTERM to the driver (pid {pid}); the engine writes a checkpoint and stops")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("command", choices=["plan", "run", "status", "stop"])
    ap.add_argument("study", type=Path, help="the study folder (with study.toml)")
    ap.add_argument("--ucmd", help="the engine; default: [executables] ucmd of the profile")
    ap.add_argument("--max-runs", type=int, help="stop after this many finished runs")
    ap.add_argument(
        "--retry-failed",
        action="store_true",
        help="run failed runs again (from their checkpoint, if they have one)",
    )
    ap.add_argument("--nice", type=int, default=10, help="niceness of builder and engine")
    ap.add_argument(
        "--stall-minutes",
        type=float,
        default=30.0,
        help="end a run whose thermo table and log stay unchanged this long; 0: never",
    )
    args = ap.parse_args(argv)
    study = load_study(args.study)
    if args.command == "plan":
        return cmd_plan(study)
    if args.command == "status":
        index = write_index(study)
        print(f"{study.dir / 'INDEX.md'}: {index['counts']}, {human(index['bytes'])}")
        return 0
    if args.command == "stop":
        return cmd_stop(study)
    engine, builder = find_executables(args.ucmd)
    driver = Driver(study, engine, builder, args.nice, args.stall_minutes)
    return driver.run(args.max_runs, args.retry_failed)


if __name__ == "__main__":
    sys.exit(main())
