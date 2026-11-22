"""T2 post-hoc check (skip length, window noise), not part of the pre-registered decision. See T2-ec-model-1M.md.

Run from the workspace root: HDF5_USE_FILE_LOCKING=FALSE ucmd-analysis/.venv/bin/python \
    docs/research/trials/T2/t2_posthoc.py OUT.json
"""

import json
import sys
from pathlib import Path

import numpy as np
from ucmd_analysis.association import contacts
from ucmd_analysis.io import read_h5md

S = Path("studies/2026-11-21_trial-t2-ec-model-1M/runs")
out = {}
for m in ("m0", "m1"):
    for s in (1, 2, 3):
        name = f"t2_{m}_s{s}"
        t = read_h5md(S / name / "T20C/out/trajectory.h5")
        a = t.system.atoms_where("Li", "Li")
        b = t.system.atoms_where("EC", "O", bonded=1)
        pf = contacts(t.positions_nm, t.boxes_nm, a, b, 0.28).sum(axis=2).mean(axis=1)
        tt = t.times_ps - t.times_ps[0]
        skip = {f"from_{k}ns": float(pf[tt >= 1000 * k].mean()) for k in (1, 2, 3)}
        dt = tt[1] - tt[0]
        n = round(500 / dt)
        w = [float(pf[i : i + n].mean()) for i in range(0, len(pf) - n + 1, n)]
        late = np.array(w[4:])  # windows from 2 ns
        out[name] = {
            **skip,
            "windows_500ps": w,
            "sd_windows_from_2ns": float(late.std(ddof=1)),
            "rel_sd": float(late.std(ddof=1) / late.mean()),
        }
        print(
            name,
            {k: round(v, 3) for k, v in skip.items()},
            " ".join(f"{x:.2f}" for x in w),
            f"rel_sd {out[name]['rel_sd']:.2f}",
            flush=True,
        )
for m in ("m0", "m1"):
    for k in ("from_1ns", "from_2ns", "from_3ns"):
        x = [out[f"t2_{m}_s{s}"][k] for s in (1, 2, 3)]
        print(m, k, f"{np.mean(x):.3f} +- {np.std(x, ddof=1) / np.sqrt(3):.3f}")
Path(sys.argv[1]).write_text(json.dumps(out, indent=1))
