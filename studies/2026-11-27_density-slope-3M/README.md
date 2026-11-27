# After SC-4: which knob moves the concentration slope? (3 M density map)

- **Label:** exploration, a map, not a fit. No parameter is chosen from it (as in the 1 M scan, whose probe values the author
  approved on 2026-11-24). Plan, reading rule and `analyze.py` are committed before the runs.
- **Why:** SC-4 failed. Its concentration slope is 0.0710 ± 0.0009 g/cm³ per M against 0.0912, and its temperature slope is right.
  Near zero salt the model is +2.8 % too dense, the solvent's offset; with salt it adds too little density, the ions. In the 1 M scan
  the ion charge scale ζ moves the density (1.1860 at ζ = 0.65, 1.2037 at 0.85) and the Li⁺ size does not.
- **Hypothesis:** the scaled charges hold the solvent around the ions too loosely (weak electrostriction), so the salt's apparent
  volume is too large. Then ζ's effect on density must grow with the salt: about 3 times larger at 3 M than at 1 M.
- **Requested by:** the author, 2026-11-27 ("analyze it, compare it with the literature, reason about it ... and submit more
  computations").

## Runs

The minimized 3 M M1 box of SC-4 (8004 atoms) with one change each: **ζ = 0.65, ζ = 0.85, EMC ε × 0.85** (`make_packages.py`, the
scan's change functions unchanged). Its unchanged run is SC-4's 3 M point. Protocol of SC-4: 0.5 fs, 3 ns, first 1 ns skipped, 20 °C.
About 5 h of GPU.

## Reading rule (fixed before the runs)

1. **ζ:** R = (dρ/dζ at 3 M) / (dρ/dζ at 1 M), each from the ζ = 0.85 and 0.65 runs. The 1 M value is the scan's, at 1 fs. SC-1
   shifts densities by about 0.2 %, nearly the same for both runs of a pair, so the derivative changes little. R ≥ 2: the effect
   **scales with the salt**, which supports the hypothesis. R ≤ 1.5: **does not scale with the salt**. In between: **partly**.
   One run per probe; a run's spread is 0.045 % (SC-1), far below the expected 3 M change of about 2 %.
2. **EMC ε:** the 3 M change divided by the 1 M change, reported. A solvent effect should be smaller at 3 M, where there is less
   EMC per volume.
3. **Not judged:** whether any ζ or ε "fixes" SC-4. Higher ζ slows the ions (scan: κ_NE exponent −3.6), lower EMC ε speeds them,
   so density and transport pull ζ different ways. That is the author's question for SC-7 and the ion model, not this map's.

**Prediction (before the runs):** dρ/dζ at 1 M is (1.2037 − 1.1860)/0.20 = 0.089 g/cm³. If it scales with c, ζ = 0.85 raises the
3 M density by about 0.027 g/cm³ (+2.0 %).

## Result (2026-11-27, all 3 runs done; `analyze.py`, output `docs/research/density-c-T/slope3M.json`)

**ζ: R = 2.05, "scales with the salt" by reading rule 1, but on the line.** dρ/dζ is 0.180 g/cm³ at 3 M against 0.088 at
1 M (scan). With one run per probe and a run's spread of about 0.045 %, R is uncertain by about ± 0.1, so it is as close to
"partly" as to clearly above 2. The prediction (+0.027 g/cm³, +2.0 % for ζ = 0.85) was close: +0.019 g/cm³ (+1.40 %), and ζ = 0.65
gives −0.017 g/cm³.

| Run (3 M, 20 °C) | ρ (g/cm³) | against Landesfeind | halves |
|---|---|---|---|
| ζ = 0.65 | 1.3192 | −3.03 % | +0.26 % |
| SC-4 point (ζ = 0.75) | 1.3365 | −2.01 % | −0.09 % |
| ζ = 0.85 | 1.3552 | −0.92 % | +0.25 % |
| EMC ε × 0.85 | 1.3149 | −3.28 % | −0.09 % |

The two ζ runs settled by SC-4's criterion (halves within 0.3 %) but both still rise between their halves, so they may read
slightly low. Their difference is less affected.

**EMC ε:** −0.0216 g/cm³ at 3 M against −0.0243 at 1 M, ratio 0.89. Smaller at 3 M, as a solvent effect should be.

**Added after the reading, not part of the rule: apparent molar volume** (`docs/research/density-c-T/v_phi_zeta.py`, output
`v_phi_zeta.json`; the model's solvent density, each run's own concentration):

| | ζ = 0.65 | 0.75 | 0.85 | dV_φ/dζ |
|---|---|---|---|---|
| 1 M (scan, 1 fs) | 79.9 | 72.4 | 65.1 cm³/mol | −74 cm³/mol |
| 3 M (0.5 fs) | 76.7 | 72.3 | 67.7 cm³/mol | −45 cm³/mol |

Experiment: 55.7 cm³/mol at 20 °C. Per mole of salt, ζ's effect at 3 M is only 60 % of that at 1 M. That is why R is 2 and
not 3: as the shells crowd, more charge buys less electrostriction. Extrapolated linearly (an estimate, not a fit), V_φ = 55.7
would need ζ ≈ 0.98 at 1 M but ζ ≈ 1.1 at 3 M, beyond full charges. **ζ alone cannot make the concentration slope right**,
and higher ζ slows the ions. Next: the anion's size (`studies/2026-11-27_pf6-size-3M`, submitted after this reading as planned).
