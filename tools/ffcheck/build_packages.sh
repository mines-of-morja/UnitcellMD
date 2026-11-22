#!/usr/bin/env bash
# Build the Li⁺ + PF₆⁻ + one-solvent packages for li_binding.py into OUTDIR.
#   tools/ffcheck/build_packages.sh OUTDIR
# M0: the library set (ADR 0009). M1: EC from the OPLS-AA types of Caleman et al. 2012, read from the
# rung-EC study's local explicit itp (not in git; see studies/2026-11-20_ec-opls-test).
set -euo pipefail
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
root=$(cd "$here/../.." && pwd)
out=${1:?usage: build_packages.sh OUTDIR}
build=$root/ucmd-builder/.venv/bin/ucmd-build
itp=$root/studies/2026-11-20_ec-opls-test/external/ec-oplsaa-explicit.itp
mkdir -p "$out"
cd "$out"
recipe() {  # name, solvent component block
    cat > "$1.toml" << EOR
format = "ucmd-build"
version = "0.1"
name = "$1"
seed = 1

[forcefield]
source = "library"
set = "opls-aa-carbonates"

[[component]]
name = "Li"
molecule = { library = "Li" }
count = 1

[[component]]
name = "PF6"
molecule = { library = "PF6" }
count = 1

$2

[box]
length_nm = 3.0

[packing]
method = "packmol"
tolerance_nm = 0.2
EOR
    "$build" build "$1.toml" -o "$1.ucsys" | tail -1
}
for s in EC DMC EMC PC; do
    recipe "m0_$s" "[[component]]
name = \"$s\"
molecule = { library = \"$s\" }
count = 1"
done
if [[ -r $itp ]]; then
    recipe m1_EC "[[component]]
name = \"EC\"
molecule = { smiles = \"O=C1OCCO1\" }
count = 1

[component.forcefield]
source = \"gromacs-top\"
file = \"$itp\"
citations = [{ what = \"EC: OPLS-AA atom types\", citation = \"C. Caleman et al., J. Chem. Theory Comput. 8, 61 (2012)\" }]"
else
    echo "skipping m1_EC: $itp not found (run the rung-EC study's make_explicit_itp.py first)" >&2
fi
