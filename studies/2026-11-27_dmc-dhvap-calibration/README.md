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

## Result (2026-11-28)

`dmc_gas_s1`, `s2` ran on soricel-pc (queue job 5e04, engine c2cc427e6a10). `s3` was orphaned at 4.15 ns when soricel went
offline; the author cancelled 5e04, and `s3` was continued on workstation-cpu from its 4.0 ns checkpoint (job
j20261128-084626-639b, engine 36b2837d56fd, 16 threads). The repeated rows 4.0–4.15 ns are counted once (last row wins). The
two engine commits differ, so `s3` is not bitwise one trajectory; statistically it is an ordinary continuation. Output:
`docs/research/emc-literature/dhvap_dmc.json`.

| | per molecule (kJ/mol) |
|---|---|
| ⟨U_gas⟩, 3 seeds | −56.70 ± 0.02 (−56.67, −56.72, −56.70) |
| ⟨U_liq⟩/N, 0.25–0.5 ns (halves −104.47, −104.43) | −104.45 |
| **ΔH_vap(DMC), model, 1 fs** | **50.23 ± 0.03** |
| reference (NIST table; not in the ledger) | 38.0 ± 0.2 |
| excess | **+12.2 (+32 %)** |
| EMC excess (step 0, against 40.5) | +12.7 (+31 %) |

- **Reading (rule fixed before the runs):** r = 12.23 / 12.67 = **0.97 ≥ 0.6: the over-cohesion is shared by the carbonate types**
  (LigParGen OPLS-AA, the same LJ types in DMC and EMC). The prediction (r ≈ 0.7–1) holds.
- DMC has a calorimetric reference; EMC's rests on vapour pressures. That both are about 31–32 % high says the EMC target
  (40–41) is not the reason for EMC's excess.
- **For SC-7:** a global correction of the carbonate types (option A) is a correction of the types, not a fix for one molecule,
  and DMC is its natural held-out test (ρ and ΔH_vap). Not judged here: densities and transport.
