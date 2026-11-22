# Force-field checks against quantum chemistry (layer 0)

Validation only, like `tools/oracle`, whose OpenMM translation of a package it uses. Nothing in
the components imports it. Plan: [forcefield-strategy.md](../../docs/research/forcefield-strategy.md),
layer 0.

```sh
tools/ffcheck/build_packages.sh OUTDIR                     # Li⁺ + PF₆⁻ + one solvent, M0 and M1
cd OUTDIR && ../tools/oracle/.venv/bin/python ../tools/ffcheck/li_binding.py *.ucsys > binding.json
tools/oracle/.venv/bin/python -m pytest tools/ffcheck      # tests (oracle venv: OpenMM, numpy, pytest)
```

## `li_binding.py`: gas-phase Li⁺–solvent binding energies

- **Definition:** E_bind = E(Li⁺·S, minimized) − E(S, minimized), with Li⁺ and S in vacuum and
  flexible. No cutoff, OpenMM Reference platform. The PF₆⁻ in the package is only there for
  neutrality; its charges and LJ ε are set to zero. For the reference energy, Li⁺ is decoupled the
  same way, so the minimizer cannot drift it.
- **Starts:** 0.2 nm out from every O along its bonds, and between pairs of ether O. The lowest
  minimum is reported, plus the lowest with the carbonyl O nearest.
- **Tests** (`test_li_binding.py`):
  - Coulomb constant against spec/units.md;
  - two unit charges at 1 nm;
  - an ion pair with LJ against the exact 1D minimum (energy to 1e-4 kJ/mol);
  - decoupled atoms change nothing;
  - the Li-charge override.

## Result, 2026-11-20

Reference: Olguin, Borodin, Ganesh, Kent, Allen, Henderson, *Phys. Chem. Chem. Phys.* 18, 164
(2016), doi:10.1039/C5CP05121E, Table 1. Numbers read from the DOE public-access manuscript
(OSTI 1238740); check them against the published table before citing them in a paper. The paper
covers EC and DMC, not EMC or PC. All values are kcal/mol, Li⁺ bound to the carbonyl O, with DMC
in its cis-cis conformer (also ours).

| | Li⁺–EC | Li⁺–DMC | Li⁺–EMC | Li⁺–PC | ΔE(EC − DMC) | ΔE(EC − EMC) |
|---|---|---|---|---|---|---|
| G4 (Olguin Table 1) | −48.1 | −41.9 | — | — | **−6.2** | — |
| range of the 11 QM methods in Table 1 | | | | | −5.5 … −7.2 | — |
| MP2/aug-cc-pVTZ, ours (`../qm`, 2026-11-21) | −48.15 | −41.27 | −41.92 | −49.86 | −6.89 | **−6.24** |
| **M0** (LigParGen EC), q_Li = 1 | −29.76 | −29.86 | −30.60 | −30.72 | **+0.10** | +0.84 |
| **M1** (OPLS-AA EC), q_Li = 1 | −31.84 | −29.86 (M0) | −30.60 (M0) | — | **−1.99** | −1.24 |
| M0, q_Li = 0.75 | −21.54 | −21.24 | −21.78 | −22.24 | −0.31 | +0.24 |
| M1, q_Li = 0.75 | −22.97 | −21.24 (M0) | −21.78 (M0) | — | −1.73 | −1.19 |

Li–O distances are 0.194–0.204 nm in all force-field cases (`results/li_binding_2026-11-20.json`);
MP2/aug-cc-pVTZ gives 0.175–0.176 nm.

**Reading:**
1. **Every fixed-charge model under-binds Li⁺ by 12–18 kcal/mol in vacuum.** This is the
   induction energy that a non-polarizable model lacks. It is common to all solvents. In the
   liquid, much of it is a many-body effect that ζ and the fitted charges are meant to absorb, so
   the absolute numbers are not the target.
2. **The difference between solvents decides the preference.** All QM methods put EC 5.5–7.2
   kcal/mol below DMC. M0 has no difference at all (+0.1); its EC is even slightly weaker than
   EMC. This is the gas-phase counterpart of the EC depletion in A4.
3. **M1 gets the sign right but recovers only about a third** (−2.0 of −6.2 kcal/mol). Against
   EMC, the cosolvent of the target electrolyte, it is a fifth: −1.24 of −6.24 kcal/mol (our
   MP2/aug-cc-pVTZ; EMC is not in Olguin's table, so this QM number is ours, at the level that
   reproduces Olguin for EC and DMC to 0.35 kcal/mol). Changing
   the EC charges alone is therefore probably not enough. The rest has to come from terms a
   fixed-charge model lacks (induction, charge transfer), or from a pair-specific Li⁺–O term
   fitted to these curves.
4. **The gas phase overstates the preference.** In Olguin's implicit-solvent calculations, the
   DMC-containing solvates gain relative to the EC ones, more so at high ε. In their BOMD at low
   salt concentration, the condensed-phase result is only a slight EC preference. This test
   checks the potential, not the shell composition. Whether M1's −2 kcal/mol is enough in the
   liquid, the M1 run of `studies/2026-11-20_li-preference-m1` shows.
