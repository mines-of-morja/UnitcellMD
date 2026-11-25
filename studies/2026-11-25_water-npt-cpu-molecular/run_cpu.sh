#!/usr/bin/env bash
# SC-3 test 2, CPU arms B and A, one run at a time, seed by seed. Safe to start again.
# Queue job (tools/queue): the worker signals only this script, so it passes SIGTERM on to the
# driver and waits until the engine has written its checkpoint.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
E=${SC3_ENGINES:-$HOME/.cache/ucmd-sc3}
export UCMD_MACHINE_PROFILE=${UCMD_MACHINE_PROFILE:-$HOME/.config/ucmd/machine-cpu.toml}
drv=
stopped=
trap 'stopped=1; [ -n "$drv" ] && kill -TERM "$drv" 2> /dev/null' TERM INT
for k in 1 2 3; do
    for arm in molecular atomic; do
        S=studies/2026-11-25_water-npt-cpu-$arm
        mkdir -p "$S/logs"
        python3 tools/study/ucmd_study.py run "$S" --only "spcfw_512_s$k/T25.01C" --nice 10 \
            --ucmd "$E/ucmd-$arm" >> "$S/logs/driver.out" 2>&1 < /dev/null &
        drv=$!
        wait "$drv"
        code=$?
        # a signal interrupts `wait`; go on waiting until the driver has really ended
        while kill -0 "$drv" 2> /dev/null; do
            wait "$drv"
            code=$?
        done
        drv=
        [ -n "$stopped" ] && exit 143
        [ "$code" -eq 0 ] || exit 1
    done
done
