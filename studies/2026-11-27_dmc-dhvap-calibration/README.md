# SC-7 calibration: is the EMC model's over-cohesion shared by the carbonate types? (DMC ΔH_vap)

- **Label:** measurement of an existing model (LigParGen OPLS-AA DMC, the same atom types as EMC). No new parameter. Plan,
  reading rule and `analyze.py` are committed before the runs.
- **Why:** SC-7 step 0 (`studies/2026-11-27_emc-dhvap-baseline`, Result) found EMC's ΔH_vap at 53.2 kJ/mol, 12.7 above the
  middle of the 40–41 working range, and 72 % of its cohesion in LJ. The EMC reference has no calorimetry behind it; DMC has
  one, and its LigParGen model uses the same LJ types (carbonyl C 0.355 / 0.293, ester O 0.29 / 0.586, carbonyl O 0.296 /
  0.879, CH₃ 0.35 / 0.276, H 0.25 / 0.126; nm / kJ/mol). DMC's density error is like EMC's (+2.3 % against +2.8 % at 25 °C,
  `docs/research/solvent-densities/README.md`). The result decides whether SC-7's global factor corrects one molecule or the
  carbonate types (`docs/design/SC-7-emc-refit.md` §6, Q7).
- **Requested by:** the author, 2026-11-27 ("go ahead" for SC-7; "continue with your work as u suggested"). Proposed in the
  design amendment. It uses no GPU: the liquid exists.
- **Method:** exactly the EMC baseline's.
  - **Gas:** one DMC molecule of the 2026-11-17 liquid package (`make_packages.py`), non-periodic, direct Coulomb, Langevin
    BAOAB at 1 fs, friction 5 ps⁻¹, 298.15 K, 10 ns, three seeds; first 0.5 ns skipped. CPU (soricel).
  - **Liquid:** `studies/2026-11-17_solvent-densities-tail-on`, DMC at 25 °C: 500 molecules, NPT, 1 fs, PME 1.4 nm with the
    tail correction (the settings of SC-1); one run of 0.5 ns, window 0.25–0.5 ns as in that study. Its two halves differ by
    0.05 kJ/mol per molecule. This is a weaker liquid average than EMC's three seeds; the error says so.
- **Reference (not in the ledger):** ΔH_vap(DMC, 298 K) = 38.0 ± 0.2 kJ/mol, NIST WebBook table (primary papers, Kozlova
  2008 and Steele 1997 in `docs/research/emc-literature/sc7-sources.md`, not read).

## Reading rule (fixed before the runs)

r = (ΔH_vap(DMC) − 38.0) / (ΔH_vap(EMC) − 40.5), both at 1 fs.

- r ≥ 0.6: the over-cohesion is **shared by the carbonate types**. A global factor is then a correction of the types,
  testable on DMC as a held-out case.
- r ≤ 0.3: it is **mainly EMC's own** (its charges or torsions). Then look at EMC's charges and conformers before a global
  LJ cut.
- otherwise: **partly shared**.
- Not judged: densities and transport.

**Prediction (before the runs):** shared (r ≈ 0.7–1). Same types, and a similar density error.

    ucmd-analysis/.venv/bin/python studies/2026-11-27_dmc-dhvap-calibration/analyze.py docs/research/emc-literature/dhvap_dmc.json
