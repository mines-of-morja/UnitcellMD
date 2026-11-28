#!/usr/bin/env bash
# T4 step 0: cost of OpenMM's pressure tensor on the GPU (bench_tensor.py), queue job.
#   bash docs/research/viscosity/run_bench.sh        (from the UnitcellMD root)
# Image and render node come from the environment, as in ucmd-openmm-docker.sh.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
W="$PWD"
IMAGE="${UCMD_OPENMM_IMAGE:-ucmd-openmm:gfx906-hip}"
DEV="${UCMD_OPENMM_DEVICES:-/dev/dri/renderD129}"
RUN=studies/2026-11-27_density-concentration-M1/runs/m1_0.1M/T20C/run.toml
OUT=docs/research/viscosity/bench
mkdir -p "$OUT"
for case in "1M studies/2026-11-25_timestep-1M-0p5fs/systems/base_s1/minimized.ucsys" \
            "EMC studies/2026-11-25_timestep-emc-0p5fs/systems/emc_500_s1/minimized.ucsys"; do
  set -- $case
  for prec in mixed double; do
    docker run --rm --init --device /dev/kfd --group-add "$(stat -c %g /dev/kfd)" \
      --device "$DEV" --group-add "$(stat -c %g "$DEV")" -v "$W:$W" -w "$W" \
      --user "$(id -u):$(id -g)" -e HOME=/tmp -e PYTHONPATH="$W/ucmd-engine/bridge/src" \
      --entrypoint python "$IMAGE" docs/research/viscosity/bench_tensor.py "$RUN" "$2" \
      --platform HIP --precision "$prec" --out "$OUT/$1_$prec.json" > /dev/null
    echo "$1 $prec done"
  done
done
