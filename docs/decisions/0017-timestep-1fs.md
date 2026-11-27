# 0017 — 1 fs time step for the flexible OPLS-AA electrolyte, with a measured band

- **Status:** accepted by the author on 2026-11-27 ("1 fs might be okay but only takes half the
  steps"), after SC-1.
- **Context:** all bonds are flexible (the GPU backend has no constraints). SC-1
  (`studies/2026-11-25_timestep-1M-0p5fs`, `docs/research/timestep/sc1.json`) measured 0.5 fs
  against 1 fs with three seeds each:
  - density ρ(0.5 fs) − ρ(1 fs): +0.227 ± 0.039 % (1 M box, 20 °C), +0.308 ± 0.030 % (pure EMC,
    25 °C), +0.141 ± 0.046 % (water);
  - configurational minus kinetic temperature: +3.7 ± 0.5 K at 1 fs, +1.7 ± 0.9 K at 0.5 fs (1 M);
  - D lower at 0.5 fs by 6–13 % (none resolved at 95 % on its own).
  By SC-1's criterion 2 the difference "matters" (above 0.1 %), and the author chooses between
  0.5 fs and a multiple time step. The benchmark (Lehnert 2025 SI, `docs/lehnert2025-si-notes.md`
  item 6) uses velocity Verlet at 1 fs. The density criteria of the trials are 1.5 %; the
  reference fit itself is good to about 0.6 % (SC-8).
- **Decision:**
  1. Runs of the flexible models use **1 fs** from now on: scans, refits (SC-7), the ion-model
     work and production. Half the cost of 0.5 fs, and the benchmark's protocol.
  2. The step's effect is a **stated systematic band**, not ignored: at 1 fs densities read
     0.2–0.3 % low and D 5–10 % high against 0.5 fs (SC-1). A density verdict within 0.3 % of its
     limit says so.
  3. Results already made at 0.5 fs (SC-1 arms, SC-4, the 3 M map) stay as they are and are
     labelled with their step. Comparisons are made at one step only, or corrected by the
     SC-1 numbers with their errors.
  4. The model that is finally reported gets one SC-1-style check at 0.5 fs (three seeds), so the
     band is measured for that model and not carried over from M1.
- **Consequences:** about half the GPU time per nanosecond. A multiple time step (RESPA) is not
  pursued now. Constraints on X–H bonds (E2.5, CPU engine only) would remove the fastest modes and
  are the standard way to a longer step; they would need the GPU backend too and are a separate
  decision.
