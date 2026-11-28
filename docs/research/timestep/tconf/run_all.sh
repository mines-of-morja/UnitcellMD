#!/usr/bin/env bash
# SC-1, "also computed, not judged": configurational temperature of every run (docs/research/water-pressure/tconf.py).
# From the workspace root. Bridge model of the runs (c2cc427, worktree ucmd-engine-scan); OpenMM CPU platform.
set -uo pipefail
export PYTHONPATH=ucmd-engine-scan/bridge/src HDF5_USE_FILE_LOCKING=FALSE
PY=ucmd-engine/bridge/.venv/bin/python
T=docs/research/water-pressure/tconf.py
O=docs/research/timestep/tconf
one() { # NAME STUDY RUN COND SKIP CUTOFF EWTOL
    [ -s "$O/$1.json" ] && return 0
    nice -n 19 "$PY" "$T" "studies/$2/systems/$3/minimized.ucsys" "studies/$2/runs/$3/$4/out" "$5" 200 "$6" "$7" "$O/$1.json"
}
for k in 1 2 3; do
    one 1M_1fs_s$k 2026-11-24_parameter-sensitivity-1M base_s$k T20C 1500 1.4 1e-5
    one 1M_0p5fs_s$k 2026-11-25_timestep-1M-0p5fs base_s$k T20C 1500 1.4 1e-5
    one emc_1fs_s$k 2026-11-25_timestep-emc-1fs emc_500_s$k T25C 500 1.4 1e-5
    one emc_0p5fs_s$k 2026-11-25_timestep-emc-0p5fs emc_500_s$k T25C 500 1.4 1e-5
    one water_1fs_s$k 2026-11-25_water-npt-gpu spcfw_512_s$k T25.01C 200 0.9 1e-6
    one water_0p5fs_s$k 2026-11-25_timestep-water-0p5fs spcfw_512_s$k T25.01C 200 0.9 1e-6
done
one water_0p25fs_s1 2026-11-25_timestep-water-0p25fs spcfw_512_s1 T25.01C 200 0.9 1e-6
