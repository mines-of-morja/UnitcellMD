#!/usr/bin/env bash
# Build the Li⁺ + PF₆⁻ + n EC (M1) + (4 − n) EMC packages for cluster_starts.py (trial T6) into OUTDIR.
#   tools/ffcheck/build_cluster_packages.sh OUTDIR
# EC from the OPLS-AA types of Caleman et al. 2012 (ADR 0014), read from the rung-EC study's local
# explicit itp (not in git; see studies/2026-11-20_ec-opls-test). EMC, Li⁺, PF₆⁻: the library set.
set -euo pipefail
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
root=$(cd "$here/../.." && pwd)
out=${1:?usage: build_cluster_packages.sh OUTDIR}
build=$root/ucmd-builder/.venv/bin/ucmd-build
itp=$root/studies/2026-11-20_ec-opls-test/external/ec-oplsaa-explicit.itp
[[ -r $itp ]] || { echo "missing $itp (run the rung-EC study's make_explicit_itp.py)" >&2; exit 1; }
mkdir -p "$out"
cd "$out"
for n in 0 1 2 3 4; do
    name="li_ec${n}_emc$((4 - n))"
    {
        printf 'format = "ucmd-build"\nversion = "0.1"\nname = "%s"\nseed = 1\n\n' "$name"
        printf '[forcefield]\nsource = "library"\nset = "opls-aa-carbonates"\n\n'
        printf '[[component]]\nname = "Li"\nmolecule = { library = "Li" }\ncount = 1\n\n'
        printf '[[component]]\nname = "PF6"\nmolecule = { library = "PF6" }\ncount = 1\n\n'
        if (( n > 0 )); then
            printf '[[component]]\nname = "EC"\nmolecule = { smiles = "O=C1OCCO1" }\ncount = %d\n\n' "$n"
            printf '[component.forcefield]\nsource = "gromacs-top"\nfile = "%s"\n' "$itp"
            printf 'citations = [{ what = "EC: OPLS-AA atom types", citation = "C. Caleman et al., J. Chem. Theory Comput. 8, 61 (2012)" }]\n\n'
        fi
        if (( n < 4 )); then
            printf '[[component]]\nname = "EMC"\nmolecule = { library = "EMC" }\ncount = %d\n\n' "$((4 - n))"
        fi
        printf '[box]\nlength_nm = 3.0\n\n[packing]\nmethod = "packmol"\ntolerance_nm = 0.2\n'
    } > "$name.toml"
    "$build" build "$name.toml" -o "$name.ucsys" | tail -1
done
