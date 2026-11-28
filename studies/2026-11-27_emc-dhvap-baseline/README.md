# SC-7 step 0: the enthalpy of vaporization of the current EMC model

- **Label:** measurement of the model as it is (LigParGen EMC in M1). No new parameter. Plan and `analyze.py` are committed
  before the runs.
- **Why:** SC-7 refits EMC to its density and ΔH_vap (author, 2026-11-27: "go ahead"). The density error is known (+2.8 % at
  25 °C, SC-1/SC-5); the model's ΔH_vap has never been computed. It is the starting point of the refit, and it tells whether
  the refit has to change mainly σ (density) or also ε (cohesion).
- **Method:** that of `studies/2026-11-20_ec-opls-test` (which reproduced Caleman 2012's EC to −0.1 % in ρ and −0.54 kJ/mol
  in ΔH_vap). ΔH_vap = ⟨U_gas⟩ − ⟨U_liq⟩/N + RT.
  - **Gas:** one EMC molecule of SC-1's liquid package (`make_packages.py`), non-periodic, no cutoff, direct Coulomb, Langevin
    BAOAB at 1 fs (ADR 0017), friction 5 ps⁻¹, 298.15 K, 10 ns, three seeds; first 0.5 ns skipped. CPU (any machine;
    ADR 0010), a few minutes per run.
  - **Liquid:** SC-1's three EMC runs (500 molecules, NPT, 25 °C), window 0.5–2 ns, at 1 fs (the protocol from now on) and,
    for the record, at 0.5 fs. No new liquid run.
- **Reference (not yet in the ledger; `docs/research/emc-literature/sc7-sources.md`):** no calorimetric ΔH_vap of EMC exists.
  Clausius–Clapeyron on the two vapour-pressure sets gives 39.9–40.2 (Goldberg 2026, raw data read) and 40.7 kJ/mol
  (Dougassa 2014, ThermoML); on DMC the same route reads 1–1.8 kJ/mol below calorimetry. Working range 40–41 ± 1 kJ/mol.
  The target value for SC-7 is the author's decision.
- **Not judged:** this is a baseline. The result is reported against the working range.
- **Prediction (before the runs):** above the range, by 1–4 kJ/mol, because the liquid is 2.8 % too dense (more cohesive). A
  weak prediction: density and cohesion need not move together.

    ucmd-analysis/.venv/bin/python studies/2026-11-27_emc-dhvap-baseline/analyze.py docs/research/emc-literature/dhvap_baseline.json

## Result (2026-11-27)

Ran on soricel-pc (job j20261127-121105-7a4d, cpu-reference, engine c2cc427e6a10), 33–39 min per 10 ns run; 12 threads were
no faster than 6 for 15 atoms. `emc_gas_s3` was stopped once at step 1 173 416 (thread count changed from 6 to 12) and
continued from its checkpoint. Output: `docs/research/emc-literature/dhvap_baseline.json`.

| | ⟨U⟩ per molecule (kJ/mol) | ΔH_vap (kJ/mol) |
|---|---|---|
| gas, 3 seeds | −21.84 ± 0.03 (−21.81, −21.91, −21.81) | |
| liquid 1 fs (SC-1) | −72.53 | **53.17 ± 0.04** |
| liquid 0.5 fs (SC-1, record only; gas at 1 fs) | −73.58 | 54.21 ± 0.04 |
| working range (literature, not in the ledger) | | 40–41 ± 1 |

- **The model is 12–13 kJ/mol (about 30 %) too cohesive.** The prediction (1–4 kJ/mol above) failed by a factor of 4: the
  density error (+2.8 %) badly understates the cohesion error.
- The gas runs' kinetic temperature is 292.4 K, below 298.15 K. That is BAOAB's known velocity bias at 1 fs with C–H bonds;
  its configurational sampling, which ⟨U⟩ uses, is not biased in this way. The EC test had the same setup.
- **Checks that the number is the model's, not the method's** (`docs/research/emc-literature/cohesion_split.py`, output
  `cohesion_split.json`, 8 frames of 0.5–2 ns per seed, three seeds):
  - OpenMM gives the gas package's start energy as the engine does (−32.793993 kJ/mol, both), and recomputes SC-1's liquid
    frames to within 0.04 kJ/mol of the stored energies (of 36 000).
  - Per molecule: intermolecular **−52.24 ± 0.04** (**LJ −37.68**, Coulomb −14.55), intramolecular −20.23 in the liquid
    against −21.84 in the gas (+1.6, distortion in the liquid); 52.24 − 1.61 + RT = 53.1, as above.
  - The LJ types are OPLS-AA's own (ether O 0.29 nm / 0.586 kJ/mol, carbonyl O 0.296 / 0.879, CH₃ 0.35 / 0.276, H 0.25 /
    0.126; carbonyl C 0.355 / 0.293).
- **Consequence for SC-7:** 72 % of the cohesion is LJ. Removing 12.7 kJ/mol through ε alone needs, to first order, ε × 0.66
  (a smaller cut once the lower density is counted); the design's map (ε × 0.90) cannot reach it. The design is amended (§6 of
  `docs/design/SC-7-emc-refit.md`); nothing is run before the author decides.
- Consistent, but not used (trials rule 2): the 1 M scan found D(EMC) and D(Li⁺) very sensitive to EMC's ε (exponent −4), and
  T4 finds the ions too slow. A 30 % over-cohesive solvent is a candidate cause.
