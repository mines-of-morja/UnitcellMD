"""Li–O distances and optimizer step counts of the T6 clusters (geometries only, no energies).

    python3 docs/research/summary_261125/extract_t6.py WORK_DIR OUT.json

WORK_DIR holds clusters_wb97x-d.json and its Psi4 outputs. Steps are the rows of optking's
convergence table, over all restarts of its step counter. No energy is read into the output.
"""

import json
import re
import sys
from pathlib import Path

work, out = Path(sys.argv[1]), Path(sys.argv[2])
STEP = re.compile(r"^\s+\d+\s+-1\d{3}\.\d+\s", re.M)
rows = []
for r in json.loads((work / "clusters_wb97x-d.json").read_text()):
    stem = Path(r["start"]).stem
    text = (work / f"clusters_wb97x-d_{stem}.out").read_text()
    rows.append({
        "cluster": stem, "n_ec": int(re.match(r"li_ec(\d)", stem).group(1)),
        "opt_coordinates": r["opt_coordinates"], "steps": len(STEP.findall(text)),
        "wall_h": round(r["wall_s"] / 3600, 2), "li_o": r["li_o_carbonyl"],
    })  # fmt: skip
out.write_text(json.dumps({"level": "wB97X-D/def2-SVP, geometries only", "clusters": rows}, indent=1) + "\n")
for r in rows:
    print(r["cluster"], r["steps"], r["wall_h"], [x["li_o_angstrom"] for x in r["li_o"]])
