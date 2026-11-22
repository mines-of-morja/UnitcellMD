"""T2 post-hoc check (the decision rule applied to shorter runs), not part of the pre-registered decision. See T2-ec-model-1M.md.

Run from the workspace root: HDF5_USE_FILE_LOCKING=FALSE ucmd-analysis/.venv/bin/python \
    docs/research/trials/T2/t2_short.py OUT.json
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
from ucmd_analysis.association import contacts
from ucmd_analysis.io import read_h5md

S = Path("studies/2026-11-21_trial-t2-ec-model-1M/runs")
cases = {
    "first_50ps": (0, 50),
    "first_250ps": (0, 250),
    "2ns_run_last_1ns": (1000, 2000),
    "3ns_run_last_1.5ns": (1500, 3000),
}
vals = {c: {"m0": [], "m1": []} for c in cases}
for m in ("m0", "m1"):
    for s in (1, 2, 3):
        t = read_h5md(S / f"t2_{m}_s{s}" / "T20C/out/trajectory.h5")
        a = t.system.atoms_where("Li", "Li")
        b = t.system.atoms_where("EC", "O", bonded=1)
        pf = contacts(t.positions_nm, t.boxes_nm, a, b, 0.28).sum(axis=2).mean(axis=1)
        tt = t.times_ps - t.times_ps[0]
        for c, (lo, hi) in cases.items():
            vals[c][m].append(float(pf[(tt >= lo) & (tt < hi)].mean()))
res = {}
for c, v in vals.items():
    (e0, s0), (e1, s1) = [
        (np.mean(v[m]), np.std(v[m], ddof=1) / math.sqrt(3)) for m in ("m0", "m1")
    ]
    same = abs(e1 - e0) <= 2 * math.hypot(s0, s1)
    closer = abs(e1 - 2.2) < abs(e0 - 2.2)
    over = e1 - 2.2 > 2 * math.hypot(s1, 0.1)
    verdict = (
        "rule 2" if over else ("rule 1" if closer and not same else ("rule 3" if same else "none"))
    )
    res[c] = {"M0": [e0, s0], "M1": [e1, s1], "per_seed": v, "verdict": verdict}
    print(f"{c:20s} M0 {e0:.3f}+-{s0:.3f}  M1 {e1:.3f}+-{s1:.3f}  -> {verdict}")
Path(sys.argv[1]).write_text(json.dumps(res, indent=1))
