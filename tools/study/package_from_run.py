"""A ready system package from the end of a run (Lehnert 2025 SI S1.1: production at the
average volume of the end of the NPT equilibration).

    python package_from_run.py RUN_DIR OUT.ucsys [--average-ps 500]

Takes the run's package (run.toml `system`), the last trajectory frame (H5MD), and the mean
volume of the last `--average-ps` of the thermo table; positions and cell are scaled
isotropically to that volume. Velocities are not copied (the next run generates them).
Needs numpy and h5py (e.g. the ucmd-analysis venv); not used by ucmd_study.py itself.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tomllib
from pathlib import Path

import h5py
import numpy as np


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run_dir", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--average-ps", type=float, default=500.0)
    args = ap.parse_args()
    run_toml = args.run_dir / "run.toml"
    with run_toml.open("rb") as fh:
        config = tomllib.load(fh)
    out_dir = args.run_dir / config.get("output", {}).get("directory", "out")
    base = args.run_dir / config["system"]
    with (out_dir / config["output"]["thermo"]["file"]).open() as fh:
        names = fh.readline().lstrip("# ").strip().split("\t")
        rows = np.loadtxt(fh)
    t, v = rows[:, names.index("time_ps")], rows[:, names.index("volume_nm3")]
    window = t >= t[-1] - args.average_ps
    v_mean = float(v[window].mean())
    with h5py.File(out_dir / config["output"]["trajectory"]["file"], "r") as fh:
        x = np.asarray(fh["particles/all/position/value"][-1], dtype=np.float64)
        box = np.asarray(fh["particles/all/box/edges/value"][-1], dtype=np.float64)
        step = int(fh["particles/all/position/step"][-1])
    scale = (v_mean / abs(np.linalg.det(box))) ** (1.0 / 3.0)
    shutil.copytree(base, args.out)
    (args.out / "velocities.npy").unlink(missing_ok=True)
    np.save(args.out / "positions.npy", x * scale)
    doc = json.loads((args.out / "system.json").read_text())
    doc["cell_nm"] = (box * scale).tolist()
    note = (
        f"from {args.run_dir} step {step}, scaled by {scale:.6f} to the mean volume "
        f"{v_mean:.4f} nm³ of the last {args.average_ps:g} ps (run.toml sha256 "
        f"{hashlib.sha256(run_toml.read_bytes()).hexdigest()[:12]})"
    )
    doc.setdefault("provenance", {})["notes"] = note
    (args.out / "system.json").write_text(json.dumps(doc, indent=1))
    print(f"{args.out}: {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
