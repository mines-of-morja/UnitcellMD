# Quantum-chemistry references (layer 0)

Validation only, like `tools/oracle` and `tools/ffcheck`. Nothing in the components uses it.
Plan: [forcefield-strategy.md](../../docs/research/forcefield-strategy.md), "QM method". The
author delegated the choice of method (2026-11-20).

## Image

Psi4 1.9.1 from conda-forge in Docker, so nothing is installed on the host:

```sh
docker build -t ucmd-psi4:1.9.1 tools/qm
```

The Dockerfile pins `libint=2.9.*` and `libxc-c=6.*`. With the solver's defaults (libint 2.14,
libxc 7), Psi4 1.9.1 does not import: it was built against libint 2.9 and needs functionals that
libxc 7 removed. Psi4 needs a user name, so runs pass `-e USER=psi4 -e HOME=/tmp` together with
`-u "$(id -u):$(id -g)"`.

## `li_binding_qm.py`: gas-phase Li⁺–solvent binding

```sh
tools/ffcheck/build_packages.sh PKG && cd PKG
../tools/oracle/.venv/bin/python ../tools/ffcheck/li_binding.py *.ucsys --q-li 1.0 --xyz start
docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp -e USER=psi4 -v "$PWD:/work" -w /work \
    ucmd-psi4:1.9.1 python li_binding_qm.py start/*.xyz --out tz.json   # copy the script in first
```

- **Start:** the force-field minimum with Li⁺ at the carbonyl O, so QM and force field are
  compared for the same binding motif.
- **Definition:** E_bind = E(Li⁺·S) − E(S) − E(Li⁺), each at its own optimized geometry
  (DF-MP2, frozen core). The counterpoise interaction energy at the complex geometry is reported
  next to it.
- **Default level:** MP2/aug-cc-pVTZ, one of the levels of Olguin et al., PCCP 18, 164 (2016),
  Table 1. It lies within 0.6 kcal/mol of their G4 values for EC and DMC.

## Check against Olguin 2016, Table 1 (kcal/mol, no counterpoise)

| level | Li⁺–EC | Li⁺–DMC (cc) | EC − DMC |
|---|---|---|---|
| Olguin, MP2/6-31+G(d,p) | −47.7 | −40.8 | −6.9 |
| **here, MP2/6-31+G(d,p)** (2026-11-21) | **−48.3** | **−40.8** | **−7.5** |
| Olguin, MP2/aug-cc-pVTZ | −47.8 | −41.3 | −6.5 |
| Olguin, G4 | −48.1 | −41.9 | −6.2 |

The small-basis check agrees to 0.6 kcal/mol per complex. The remaining difference can come from
density fitting or the conformer found from our start. Counterpoise interaction energies at the
complex geometry, at this level: EC −49.7, DMC −42.0. They exclude the solvent's deformation
energy, so they are more negative than E_bind.

### Frozen core and bare Li⁺ (fixed 2026-11-21)

Psi4's `freeze_core = True` unfreezes the outermost core shell when freezing it would leave no
valence electrons. Bare Li⁺ was therefore correlated, while the Li 1s inside the complex stayed
frozen. That made E_bind too weak by the Li⁺ 1s² correlation energy: 0.3 kcal/mol at
6-31+G(d,p), which went unnoticed, and 6.9 kcal/mol at aug-cc-pVTZ (EC −41.3 instead of −48.2),
which the comparison with Olguin caught. The script now takes the SCF energy for any species
without active electrons, and does the counterpoise correction by hand so that Li⁺ in the dimer
basis is treated the same way. Rerun with the fix at 6-31+G(d,p): EC −48.30, DMC −40.85
kcal/mol, the same as the first run corrected by hand from its output.
