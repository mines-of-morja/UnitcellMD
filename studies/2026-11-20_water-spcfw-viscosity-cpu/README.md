# 2026-11-20 — rung W, P5: Green–Kubo viscosity of SPC/Fw (CPU)

- **Run:** NVT at Wu 2006's η conditions (ρ = 1.012 g/cm³, 300.2 K), 512 molecules (216 do not fit the cutoff), 4 ns at
  1 fs. Thermo every 2 fs with the pressure tensor (spec 0.1.1), engine of branch
  `e29-pressure-tensor`.
- **Analysis:** `ucmd-analyze viscosity out/thermo.tsv --temperature-K 300.2 --skip-ps 200`.
- **Target:** Wu's 0.75 cP (periodic perturbation method, 864 molecules, inaccuracy ≈ 0.01).
  Green–Kubo is an independent method for the same property.
