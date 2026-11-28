#!/usr/bin/env bash
# SC-3 test 2, CPU arms B and A, one run at a time, seed by seed. Safe to start again.
# Queue job (tools/queue): on a stop this script passes SIGTERM on to the driver, once, and waits until
# the engine has written its checkpoint. The driver runs in its own session (setsid): a worker
# that signals the whole process group would otherwise reach it a second time, and the driver kills
# the engine on a second signal.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
E=${SC3_ENGINES:-$HOME/.cache/ucmd-sc3}
export UCMD_MACHINE_PROFILE=${UCMD_MACHINE_PROFILE:-$HOME/.config/ucmd/machine-cpu.toml}
drv=
stopped=
stop() {
    [ -n "$stopped" ] && return  # only the first one
    stopped=1
    [ -n "$drv" ] && kill -TERM "$drv" 2> /dev/null
}
trap stop TERM INT
for k in 1 2 3; do
    for arm in molecular atomic; do
        S=studies/2026-11-25_water-npt-cpu-$arm
        [ -n "$stopped" ] && exit 143
        mkdir -p "$S/logs"
        setsid python3 tools/study/ucmd_study.py run "$S" --only "spcfw_512_s$k/T25.01C" --nice 10 \
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
