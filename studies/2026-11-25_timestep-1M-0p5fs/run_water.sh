#!/usr/bin/env bash
# SC-1, the water arms, for the job queue (tag gpu-hip-double): the engine, bridge and precision of
# ../2026-11-25_water-npt-gpu, which the plain study tag does not select. Finished runs are skipped.
#   run_water.sh 0p5fs | 0p25fs
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
S=studies/2026-11-25_timestep-water-${1:?0p5fs or 0p25fs}
[ -f "$S/study.toml" ] || { echo "no $S" >&2; exit 1; }
E=${SC1_ENGINES:-$HOME/.cache/ucmd-sc3}
export UCMD_MACHINE_PROFILE=${SC1_GPU_PROFILE:-$HOME/.config/ucmd/machine-gpu-double-scan.toml}
[ -f "$UCMD_MACHINE_PROFILE" ] || { echo "no $UCMD_MACHINE_PROFILE" >&2; exit 1; }
mkdir -p "$S/logs"
# exec: a SIGTERM from the queue worker reaches the driver itself
exec python3 tools/study/ucmd_study.py run "$S" --retry-failed --stall-minutes 10 --nice 10 \
    --ucmd "$E/ucmd-atomic" >> "$S/logs/driver.out" 2>&1 < /dev/null
