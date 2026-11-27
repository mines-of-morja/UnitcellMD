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
