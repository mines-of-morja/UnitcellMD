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
