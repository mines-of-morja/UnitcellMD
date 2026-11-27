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
