"""Run V-3 arms on the GPU, for the job queue (one command job per README "Jobs" letter). Standard library only.

    python3 studies/2026-11-28_v3-thermo-consistency/run.py JOB      # e.g. A; from the workspace root

- Engine and bridge: the worktree ../ucmd-engine-consist (branch v3-consistency = ucmd-engine main 36b2837),
  its release `ucmd` and its bridge in the HIP image. The machine profile is written into logs/ at the start
  (not a user profile; the queue's profiles are not touched).
- Resumable: a finished arm (status.json "done") is skipped; an interrupted one continues from its checkpoint.
- Watchdog: no new thermo row for STALL_MIN minutes (the GPU hang) ends the engine and continues from the
  checkpoint, at most RETRIES times per arm.
- A SIGTERM (queue stop) is passed on to the engine, which checkpoints; the job then exits 143.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from arms import ARMS, make_run_toml

WORKSPACE = HERE.parents[1]
WORKTREE = WORKSPACE / "ucmd-engine-consist"
UCMD = WORKTREE / "target/release/ucmd"
BRIDGE = WORKTREE / "bridge/docker/ucmd-openmm-docker-hip.sh"
STALL_MIN = 10.0
RETRIES = 4
NICE = 10
stop = False


def on_term(signum, frame):
    global stop
    stop = True


def profile(precision: str) -> Path:
    path = HERE / "logs" / f"machine-hip-{precision}.toml"
    path.parent.mkdir(exist_ok=True)
    path.write_text(f'[executables]\nucmd-openmm = "{BRIDGE}"\n\n[backend]\nkind = "openmm"\nplatform = "HIP"\n'
                    f'precision = "{precision}"\n')  # fmt: skip
    return path


def status(d: Path) -> dict:
    try:
        return json.loads((d / "status.json").read_text())
    except (OSError, ValueError):
        return {}


def write_status(d: Path, **kw) -> None:
    s = status(d) | kw | {"updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (d / "status.json").write_text(json.dumps(s, indent=1, sort_keys=True) + "\n")


def run_arm(arm, prof: Path) -> int:
    d = HERE / "arms" / arm.name
    d.mkdir(parents=True, exist_ok=True)
    toml = make_run_toml(arm)
    if (d / "run.toml").exists() and (d / "run.toml").read_text() != toml:
        print(f"{arm.name}: run.toml differs from arms.py; refusing to mix two protocols", flush=True)
        return 2
    (d / "run.toml").write_text(toml)
    if status(d).get("state") == "done":
        print(f"{arm.name}: done, skipped", flush=True)
        return 0
    env = dict(os.environ, UCMD_MACHINE_PROFILE=str(prof), HDF5_USE_FILE_LOCKING="FALSE")
    for attempt in range(RETRIES + 1):
        ckpt = d / "out/checkpoint.ucchk"
        args = ["nice", "-n", str(NICE), str(UCMD), "run", "run.toml"]
        if ckpt.exists():
            args += ["--restart", "out/checkpoint.ucchk"]
        write_status(d, state="running", attempt=attempt, started=time.time())
        print(f"{arm.name}: attempt {attempt}: {' '.join(args[3:])}", flush=True)
        with (d / "run.log").open("a") as log:
            p = subprocess.Popen(args, cwd=d, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            last, stalled = time.time(), False
            thermo = d / "out/thermo.tsv"
            while p.poll() is None:
                time.sleep(5)
                if stop:
                    os.killpg(p.pid, signal.SIGTERM)
                    p.wait()
                    write_status(d, state="stopped", exit=p.returncode)
                    return 143
                with_rows = thermo.exists() and thermo.stat().st_mtime
                if with_rows and with_rows > last:
                    last = with_rows
                if time.time() - last > 60 * STALL_MIN:
                    stalled = True
                    os.killpg(p.pid, signal.SIGTERM)
                    try:
                        p.wait(timeout=60)
                    except subprocess.TimeoutExpired:
                        os.killpg(p.pid, signal.SIGKILL)
                        p.wait()
        if p.returncode == 0 and not stalled:
            write_status(d, state="done", exit=0, finished=time.time())
            print(f"{arm.name}: done", flush=True)
            return 0
        write_status(d, state="stalled" if stalled else "failed", exit=p.returncode)
        print(f"{arm.name}: {'stalled' if stalled else f'exit {p.returncode}'}", flush=True)
        if not stalled and not ckpt.exists():
            return 1  # a failure before the first checkpoint is not a hang: do not retry blindly
    return 1


def main() -> int:
    signal.signal(signal.SIGTERM, on_term)
    signal.signal(signal.SIGINT, on_term)
    job = sys.argv[1]
    arms = [a for a in ARMS if a.job == job]
    if not arms:
        raise SystemExit(f"no arms in job {job!r}")
    worst = 0
    for arm in arms:
        missing = [p for p in (UCMD, BRIDGE, HERE / "packages" / f"{arm.package}.ucsys") if not p.exists()]
        if missing:
            print(f"{arm.name}: missing {missing}", flush=True)
            worst = max(worst, 1)
            continue
        code = run_arm(arm, profile(arm.precision))
        if code == 143:
            return 143
        worst = max(worst, code)
    return worst


if __name__ == "__main__":
    sys.exit(main())
