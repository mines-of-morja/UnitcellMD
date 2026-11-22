import json, subprocess, sys, statistics as st
from pathlib import Path
import h5py, numpy as np
A = "ucmd-analysis/.venv/bin/ucmd-analyze"
RUNS = {"M0": ["2026-11-20_li-preference/runs/lipf6_in_ec-emc_1-1n"] + [f"2026-11-21_li-preference-replicas/runs/m0_r{i}" for i in (1,2,3)],
        "M1": ["2026-11-20_li-preference-m1/runs/m1_lipf6_in_ec-emc_1-1n"] + [f"2026-11-21_li-preference-replicas/runs/m1_r{i}" for i in (1,2,3)]}
def ana(*a):
    return json.loads(subprocess.run([A, *a], capture_output=True, text=True, check=True).stdout)
out = {}
for model, runs in RUNS.items():
    for r in runs:
        t = f"studies/{r}/T20C/out/trajectory.h5"
        with h5py.File(t) as h:
            tm = h["particles/all/position/time"][:]
        dt = np.diff(tm)
        cont = f"{len(tm)} frames, {tm[0]:.0f}-{tm[-1]:.0f} ps, dt {dt.min():.3f}-{dt.max():.3f}"
        s1 = ana("shell", t, "--skip-ps", "1000", "--a", "Li:Li", "--b", "EC:O:1", "--b", "EMC:O:1", "--b", "PF6:P", "--r-cut-nm", "0.28", "--r-cut-nm", "0.28", "--r-cut-nm", "0.28")["mean_contacts"]
        s2 = ana("shell", t, "--skip-ps", "1000", "--a", "Li:Li", "--b", "EC:O:1", "--b", "EMC:O:1", "--b", "PF6:P",
                 "--r-cut-nm", "0.516", "--r-cut-nm", "0.516", "--r-cut-nm", "0.516")["mean_contacts"]
        res = {b: ana("residence", t, "--a", "Li:Li", "--b", b, "--r-cut-nm", "0.30") for b in ("EC:O:1", "EMC:O:1")}
        row = dict(model=model, run=r.split("/")[-1], frames=cont,
                   ec1=s1["EC:O:1"], emc1=s1["EMC:O:1"], pf6_1=s1["PF6:P"],
                   share1=100*s1["EC:O:1"]/(s1["EC:O:1"]+s1["EMC:O:1"]),
                   ec2=s2["EC:O:1"], emc2=s2["EMC:O:1"], pf6_2=s2["PF6:P"],
                   share2=100*s2["EC:O:1"]/(s2["EC:O:1"]+s2["EMC:O:1"]),
                   tc_ec=res["EC:O:1"]["tau_continuous_ps"], tc_emc=res["EMC:O:1"]["tau_continuous_ps"],
                   ti_ec=res["EC:O:1"]["tau_intermittent_ps"], ti_emc=res["EMC:O:1"]["tau_intermittent_ps"],
                   ti_emc_decayed=res["EMC:O:1"]["tau_intermittent_decayed"])
        out[row["run"]] = row
        print(json.dumps(row), flush=True)
json.dump(out, open(sys.argv[1], "w"), indent=1)
