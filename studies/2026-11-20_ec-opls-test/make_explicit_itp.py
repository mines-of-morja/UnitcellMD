"""Write a GROMACS topology with every parameter explicit, read by OpenMM from one that uses type
lookup (`[ bondtypes ]` etc.), so that the builder's `gromacs-top` source can read it.

    <bridge venv>/bin/python make_explicit_itp.py external/96-49-1.top external/ec-oplsaa-explicit.itp

- Why: Caleman et al. 2012 (virtualchemistry.org) give EC as OPLS-AA atom types whose bonded
  parameters come from `oplsaaff.itp` by type. The builder reads explicit parameters only.
- How: OpenMM's GromacsTopFile does the type lookup (it is also our oracle's reader). Its System
  is written back term by term:
  - bonds and angles (½k forms, as GROMACS);
  - Ryckaert–Bellemans dihedrals (funct 3);
  - one atom type per atom with that atom's σ and ε;
  - charges, masses;
  - the 1-4 pairs.
- Checks before writing:
  - every OpenMM 1-4 exception equals fudge × the geometric combination of the two atoms, so
    `[ pairs ]` without parameters means the same;
  - the exclusions are the 1-2 and 1-3 neighbours.
- The output is derived from files without a stated licence. It stays in `external/` (not in
  git). The citation travels in the recipe.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import openmm as mm
from openmm import app, unit

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
top = app.GromacsTopFile(str(src))
system = top.createSystem(nonbondedMethod=app.NoCutoff)
forces = {type(f).__name__: f for f in system.getForces()}
# With comb-rule 3 (geometric σ), OpenMM keeps only Coulomb in NonbondedForce and puts the LJ in a
# CustomNonbondedForce (per atom C = √(4εσ⁶), A = √(4εσ¹²)) plus a CustomBondForce for 1-4 LJ.
known = {"HarmonicBondForce", "HarmonicAngleForce", "RBTorsionForce", "NonbondedForce",
         "CustomNonbondedForce", "CustomBondForce", "CMMotionRemover"}  # fmt: skip
extra = set(forces) - known
if extra or "PeriodicTorsionForce" in forces:
    sys.exit(f"terms this script does not write: {sorted(extra)}")
nb = forces["NonbondedForce"]
lj = forces["CustomNonbondedForce"]
lj14 = forces["CustomBondForce"]
if lj.getEnergyFunction().replace(" ", "") != "A1*A2/r^12-C1*C2/r^6":
    sys.exit(f"unexpected LJ form {lj.getEnergyFunction()}")
n = system.getNumParticles()
atoms = list(top.topology.atoms())
fudge_lj = fudge_qq = 0.5  # oplsaaff.itp [ defaults ]: 1 3 yes 0.5 0.5 (checked below)
q, sig, eps = [], [], []
cc, aa = [], []
for i in range(n):
    c, _s, e = nb.getParticleParameters(i)
    if e.value_in_unit(unit.kilojoule_per_mole) != 0.0:
        sys.exit("LJ found in NonbondedForce as well")
    q.append(c.value_in_unit(unit.elementary_charge))
    ci, ai = lj.getParticleParameters(i)  # (C, A) in kJ/mol·nm⁶ and ·nm¹², square roots
    cc.append(ci)
    aa.append(ai)
    if ci == 0.0 and ai == 0.0:
        sig.append(0.0)
        eps.append(0.0)
    else:
        sig.append((ai / ci) ** (1.0 / 3.0))
        eps.append(ci**4 / (4.0 * ai**2))
lj14_pairs = {}
for k in range(lj14.getNumBonds()):
    i, j, (c6, c12) = lj14.getBondParameters(k)
    if not (math.isclose(c6, fudge_lj * cc[i] * cc[j], rel_tol=1e-9, abs_tol=1e-15)
            and math.isclose(c12, fudge_lj * aa[i] * aa[j], rel_tol=1e-9, abs_tol=1e-20)):  # fmt: skip
        sys.exit(f"1-4 LJ {i}-{j} is not fudge × geometric combination")
    lj14_pairs[frozenset((i, j))] = True

bonds = []
f = forces["HarmonicBondForce"]
for k in range(f.getNumBonds()):
    i, j, r0, kb = f.getBondParameters(k)
    bonds.append((i, j, r0.value_in_unit(unit.nanometer),
                  kb.value_in_unit(unit.kilojoule_per_mole / unit.nanometer**2)))  # fmt: skip
neighbours = {i: set() for i in range(n)}
for i, j, *_ in bonds:
    neighbours[i].add(j)
    neighbours[j].add(i)
angles = []
f = forces["HarmonicAngleForce"]
for k in range(f.getNumAngles()):
    i, j, l, th, ka = f.getAngleParameters(k)
    angles.append((i, j, l, math.degrees(th.value_in_unit(unit.radian)),
                   ka.value_in_unit(unit.kilojoule_per_mole / unit.radian**2)))  # fmt: skip
rb = []
f = forces["RBTorsionForce"]
for k in range(f.getNumTorsions()):
    i, j, l, m, *c = f.getTorsionParameters(k)
    rb.append((i, j, l, m, [x.value_in_unit(unit.kilojoule_per_mole) for x in c]))

pairs = []
for k in range(nb.getNumExceptions()):
    i, j, qq, s, e = nb.getExceptionParameters(k)
    qq = qq.value_in_unit(unit.elementary_charge**2)
    s, e = s.value_in_unit(unit.nanometer), e.value_in_unit(unit.kilojoule_per_mole)
    bonded = j in neighbours[i] or bool(neighbours[i] & neighbours[j])
    if bonded:
        if qq != 0.0 or e != 0.0:
            sys.exit(f"exclusion {i}-{j} carries parameters")
        continue
    if e != 0.0 or not math.isclose(qq, fudge_qq * q[i] * q[j], rel_tol=1e-9, abs_tol=1e-12):
        sys.exit(f"1-4 Coulomb {i}-{j} is not fudge × qᵢqⱼ: {qq}")
    if frozenset((i, j)) not in lj14_pairs:
        sys.exit(f"1-4 pair {i}-{j} has Coulomb but no LJ")
    pairs.append((i, j))
if len(pairs) != len(lj14_pairs):
    sys.exit("1-4 LJ pairs without Coulomb")

out = [
    f"; explicit-parameter copy of {src.name}, written by make_explicit_itp.py (OpenMM "
    f"{mm.__version__} GromacsTopFile)",
    "; source: C. Caleman et al., J. Chem. Theory Comput. 8, 61 (2012); OPLS-AA atom types",
    "[ defaults ]",
    "; nbfunc comb-rule gen-pairs fudgeLJ fudgeQQ",
    f"1 3 yes {fudge_lj} {fudge_qq}",
    "",
    "[ atomtypes ]",
    "; name at.num mass charge ptype sigma epsilon",
]
for i, a in enumerate(atoms):
    mass = system.getParticleMass(i).value_in_unit(unit.dalton)
    out.append(f"t{i + 1} {a.element.atomic_number} {mass:.6f} 0.0 A {sig[i]:.10e} {eps[i]:.10e}")
out += ["", "[ moleculetype ]", "; name nrexcl", "EC 3", "", "[ atoms ]",
        "; nr type resnr res atom cgnr charge mass"]  # fmt: skip
for i, a in enumerate(atoms):
    mass = system.getParticleMass(i).value_in_unit(unit.dalton)
    out.append(f"{i + 1} t{i + 1} 1 EC {a.name}{i + 1} {i + 1} {q[i]:.10f} {mass:.6f}")
out += ["", "[ bonds ]"]
out += [f"{i + 1} {j + 1} 1 {r0:.10e} {kb:.10e}" for i, j, r0, kb in bonds]
out += ["", "[ pairs ]"]
out += [f"{i + 1} {j + 1} 1" for i, j in sorted(pairs)]
out += ["", "[ angles ]"]
out += [f"{i + 1} {j + 1} {l + 1} 1 {th:.10f} {ka:.10e}" for i, j, l, th, ka in angles]
out += ["", "[ dihedrals ]"]
out += [f"{i + 1} {j + 1} {l + 1} {m + 1} 3 " + " ".join(f"{x:.10e}" for x in c)
        for i, j, l, m, c in rb]  # fmt: skip
dst.write_text("\n".join(out) + "\n")
print(f"wrote {dst}: {n} atoms, {len(bonds)} bonds, {len(angles)} angles, {len(rb)} RB "
      f"dihedrals, {len(pairs)} pairs")  # fmt: skip
