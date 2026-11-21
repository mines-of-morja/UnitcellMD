# Li⁺ preference, replicas of M0 and M1 (strategy step S2, statistics), prepared 2026-11-21

- **Question:** is the M1 shift real? With one ion each, M1 (OPLS-AA EC) gave EC 31 ± 7 % of
  the first-shell carbonyl O and M0 (LigParGen EC) 19 ± 4 % (SEM over 4 × 1 ns blocks, which are
  correlated). That is 1.4 standard errors (`../2026-11-20_li-preference-m1/README.md`).
- **Design:** three more independent starts per model: packing seeds 20261121–23 (new start
  structures) and run seeds derived from the run ids (new velocities). Systems, protocol and
  analysis are those of `2026-11-20_li-preference-m1` and of the A4 1:1 run, unchanged: one
  LiPF₆ pair (ζ = 0.75) in 250 EC + 250 EMC, 5 ns NPT at 1 atm and 20 °C, last 4 ns analysed.
- **Analysis:** per run, the EC share of the carbonyl O within 0.28 nm of Li⁺ and within
  0.516 nm, and the EC and EMC residence times. With the two existing runs, each model then has
  four independent runs. The comparison uses the spread between runs, not the block SEM.
- **Reading:** if the four M1 runs all lie above the four M0 runs, the carbonyl charges move the
  preference. The size of the shift then sets how much a pair-specific Li⁺–O term still has to
  add towards the QM EC–DMC difference (layer 0, `tools/ffcheck/README.md`).
- **Cost:** 6 runs of about 1 h each on HIP (M1 took 58 min), GPU queue 6.
- **Bridge:** all runs use the e37-identity bridge, the same as the M1 run, so the runs stay
  consistent. That bridge takes OpenMM's LJ tail correction as is: it counts N(N+1)/2 pairs over
  all atoms, including H without LJ, while the engine weights the pairs by atom class. That
  difference made SPC/Fw water fail the start-up check. It is fixed on the bridge branch
  e25-constraints (afbc3b2). For these boxes the error is of order 1/N of the tail: the EC
  systems pass the energy check at 2.7e-7. It has no visible effect on the shell counts.

## Result, 2026-11-21

All six runs finished on HIP (queue 6), about 1 h each. m1_r2 was ended at 3340 ps by the
GPU-hang telemetry (bridge in `kfd_wait_on_events`, thermo silent 191 s) and continued from its
checkpoint. All eight trajectories (with the two earlier runs) have 2501 frames at 2 ps without a
gap. The shell values use the last 4 ns; the residence times the whole 5 ns, as in the M1 study.

| run | first shell (< 0.28 nm) EC / EMC | EC share | within 0.516 nm EC / EMC / PF₆ | EC share | τ_cont EC / EMC (ps) | τ_int EC / EMC (ps) |
|---|---|---|---|---|---|---|
| M0, A4 run | 0.86 / 3.63 | 19.2 % | 1.63 / 3.97 / 0.00 | 29.1 % | 28 / 286 | 127 / ≥ 2498¹ |
| M0, m0_r1 | 0.70 / 3.78 | 15.5 % | 1.62 / 4.01 / 0.00 | 28.8 % | 17 / 302 | 77 / 1282 |
| M0, m0_r2 | 0.86 / 3.26 | 20.8 % | 1.56 / 3.49 / 0.40 | 30.9 % | 24 / 479 | 131 / 1755 |
| M0, m0_r3 | 0.64 / 3.56 | 15.3 % | 1.52 / 3.80 / 0.22 | 28.5 % | 16 / 382 | 100 / 2048 |
| M1, first run | 1.41 / 3.19 | 30.7 % | 2.20 / 3.44 / 0.00 | 39.0 % | 42 / 303 | 272 / 2043 |
| M1, m1_r1 | 1.41 / 3.20 | 30.6 % | 2.33 / 3.46 / 0.00 | 40.2 % | 38 / 219 | 185 / 1720 |
| M1, m1_r2 | 1.73 / 2.85 | 37.8 % | 2.50 / 3.19 / 0.00 | 43.9 % | 41 / 247 | 366 / 1926 |
| M1, m1_r3 | 1.03 / 3.51 | 22.7 % | 1.92 / 3.79 / 0.00 | 33.7 % | 41 / 272 | 149 / 1283 |

¹ the correlation function had not decayed within the window.

Mean ± standard error over the four runs per model (n = 4; difference M1 − M0 with its
combined standard error):

| quantity | M0 | M1 | M1 − M0 |
|---|---|---|---|
| EC share, first shell | 17.7 ± 1.4 % | 30.4 ± 3.1 % | **+12.7 ± 3.4** (3.8 SE) |
| EC share within 0.516 nm | 29.3 ± 0.5 % | 39.2 ± 2.1 % | **+9.9 ± 2.2** (4.5 SE) |
| EC carbonyl O in the first shell | 0.76 ± 0.06 | 1.40 ± 0.14 | +0.63 ± 0.15 |
| continuous EC residence | 21 ± 3 ps | 40 ± 1 ps | +19 ± 3 ps |
| continuous EMC residence | 362 ± 44 ps | 260 ± 18 ps | −102 ± 48 ps |

**Reading:**
1. **The M1 shift is real.** All four M1 runs lie above all four M0 runs, in the first shell
   (M0 15.3–20.8 %, M1 22.7–37.8 %) and within 0.516 nm (28.5–30.9 % against 33.7–43.9 %). The
   EC residence time doubles in every M1 run. This was the criterion set before the runs.
2. **The spread between runs is the real uncertainty.** The first M1 run's block SEM (± 7 %)
   was the right size; the spread of the four M1 runs is 22.7–37.8 %. One ion samples few
   shell exchanges in 4 ns.
3. **M1 still keeps EC below its share of the molecules** (50 %): 30 % in the first shell. The
   carbonyl charges move the preference in the direction of QM, as layer 0 predicted (M1
   recovers −1.2 of −6.2 kcal/mol of the gas-phase EC − EMC difference), but not all the way.
   Whether that matters for the target electrolyte is a question for 1 M, against the DRS
   estimate (about 2.2 bound EC per Li⁺, `docs/research/summary/`).
4. **Caveat:** two of the M0 replicas had PF₆⁻ within 0.516 nm for part of the time (0.22 and
   0.40 on average), no M1 run did. With one ion pair per box this is an occasional event; it
   does not enter the EC share, which counts carbonyl O only.

**An error in the M1 study's commands:** `../2026-11-20_li-preference-m1/README.md` gave the
first-shell command without `--r-cut-nm`. The CLI then picks the first minimum of each g(r)
separately (EC 0.3175, EMC 0.2875 nm), which skews the share. The table there used 0.28 nm for
both, as stated; the command is now corrected. The first analysis of these replicas used the
wrong command and was redone.

Analysis: `analysis/replicas.py` (writes `analysis/replicas.json`), run from the workspace root
with the ucmd-analysis venv:

```sh
HDF5_USE_FILE_LOCKING=FALSE ucmd-analysis/.venv/bin/python \
    studies/2026-11-21_li-preference-replicas/analysis/replicas.py OUT.json
```
