#!/usr/bin/env bash
# SC-3 test 2, CPU arms B and A, one run at a time, seed by seed. Safe to start again.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
E=${SC3_ENGINES:-$HOME/.cache/ucmd-sc3}
export UCMD_MACHINE_PROFILE=${UCMD_MACHINE_PROFILE:-$HOME/.config/ucmd/machine-cpu.toml}
for k in 1 2 3; do
    for arm in molecular atomic; do
        S=studies/2026-11-25_water-npt-cpu-$arm
        mkdir -p "$S/logs"
        python3 tools/study/ucmd_study.py run "$S" --only "spcfw_512_s$k/T25.01C" --nice 10 \
            --ucmd "$E/ucmd-$arm" >> "$S/logs/driver.out" 2>&1 < /dev/null || exit 1
    done
done
