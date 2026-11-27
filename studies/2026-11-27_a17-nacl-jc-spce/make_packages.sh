#!/usr/bin/env bash
# Build and minimize the four start packages (CPU, minutes). Needs the ucmd-builder branch
# claude/a17-nacl-spce (set nacl-jc-spce) in ../../ucmd-builder-nacl and the engine of the GPU
# worker (rigid-water RATTLE and FIRE on the constraint manifold, ucmd 2ea7e82).
# Usage: bash make_packages.sh   (from anywhere; writes packages/*.ucsys, refuses to overwrite)
set -euo pipefail
cd "$(dirname "$0")"
WS=../..
BUILDER_SRC=${A17_BUILDER_SRC:-$WS/ucmd-builder-nacl/src}
PY=${A17_BUILDER_PY:-$WS/ucmd-builder/.venv/bin/python}
UCMD=${A17_UCMD:-$HOME/.cache/ucmd-scan/ucmd}
mkdir -p packages work
for r in recipes/*.toml; do
    n=$(basename "$r" .toml)
    [ -e "packages/$n.ucsys" ] && { echo "exists: packages/$n.ucsys"; continue; }
    rm -rf "work/$n" && mkdir -p "work/$n"
    PYTHONPATH="$BUILDER_SRC" "$PY" -m ucmd_builder.cli build "$r" -o "work/$n/built.ucsys" -q
    sed "s|SYSTEM|built.ucsys|" minimize.toml > "work/$n/minimize.toml"
    (cd "work/$n" && "$UCMD" minimize minimize.toml --out minimized.ucsys > minimize.log 2>&1)
    mv "work/$n/minimized.ucsys" "packages/$n.ucsys"
    echo "packages/$n.ucsys"
done
