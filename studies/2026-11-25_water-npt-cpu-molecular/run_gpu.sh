#!/usr/bin/env bash
# SC-3 test 2, GPU arm G. Refuses to start while another container or queue script uses the GPU.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
E=${SC3_ENGINES:-$HOME/.cache/ucmd-sc3}
export UCMD_MACHINE_PROFILE=${SC3_GPU_PROFILE:-$HOME/.config/ucmd/machine-gpu-double-scan.toml}
if [ -n "$(docker ps -q --filter ancestor=ucmd-openmm:gfx906-hip)" ] || pgrep -f '[g]pu-queue[0-9]*\.sh' > /dev/null; then
    echo "the GPU is in use" >&2
    exit 1
fi
[ -f "$UCMD_MACHINE_PROFILE" ] || { echo "no $UCMD_MACHINE_PROFILE" >&2; exit 1; }
S=studies/2026-11-25_water-npt-gpu
mkdir -p "$S/logs"
python3 tools/study/ucmd_study.py run "$S" --retry-failed --stall-minutes 10 --nice 10 \
    --ucmd "$E/ucmd-atomic" >> "$S/logs/driver.out" 2>&1 < /dev/null
