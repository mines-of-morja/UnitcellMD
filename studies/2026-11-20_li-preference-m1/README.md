# Li⁺ preference with OPLS-AA EC (strategy step S2, model M1), prepared 2026-11-20

- **Question:** does the EC carbonyl model decide which carbonyl binds Li⁺? Without salt
  crowding, model M0 (LigParGen EC, carbonyl O −0.393 e) puts EC at only about 21 % of the
  carbonyl O in the first Li⁺ shell of an EC:EMC 1:1 mixture (A4, preliminary, see below).
  M1 swaps only EC for the OPLS-AA atom types of Caleman et al. 2012 (carbonyl O −0.50 e,
  C +0.86 e, ring O −0.45 e).
- **Plan:** [docs/research/forcefield-strategy.md](../../docs/research/forcefield-strategy.md),
  level M1 (approved by the author as a test set on 2026-11-20; not the working horse).
- **System:** one LiPF₆ pair in 250 EC + 250 EMC (1:1 by molecules), ζ = 0.75. Li⁺, PF₆⁻ and EMC
  as in M0. Both sources use OPLS conventions (geometric mixing, 1-4 scales 0.5/0.5).
- **EC parameters:** the rung-EC study's local explicit copy
  (`../2026-11-20_ec-opls-test/external/ec-oplsaa-explicit.itp`; the downloaded files carry no
  licence and stay out of git). The trial build gave 6258 atoms and passed `ucmd-build check`;
  the EC charges in the package are the Caleman values.
- **Protocol:** identical to `studies/2026-11-20_li-preference` (A4): 1 fs, Nosé–Hoover chain
  τ = 0.1 ps, C-rescale at 1 atm, 1.4 nm, PME 1e-5, tail correction, 5 ns NPT, GPU mixed
  precision, a frame every 2 ps. Runs on the identity-fixed bridge (queue 4, after queue 3), so
  residence times need no repair.
- **Backend:** the shared profile switched to OpenMM 8.5 with the HIP platform on 2026-11-20
  (author-approved, against the OpenCL hangs). M1 runs on HIP; M0 (A4) ran on OpenCL with
  OpenMM 8.3. Both pass the per-run conformance check against the CPU engine (about 1e-8). The
  backend difference is far below the statistical noise of a single-ion shell, so the comparison
  stands.
- **Comparison (M0):** the 1:1 run of the A4 study, finished 2026-11-20 (5 ns, OpenCL, no label
  swaps). Over 1–5 ns: first shell EC O=C 0.89, EMC O=C 3.65 (**EC 20 %**); within 0.516 nm
  (Lehnert's rs) EC 1.63, EMC 3.97 (EC 29 %). Continuous residence at Li⁺: EC 24 ps, EMC 250 ps.
  In pure EC the same Li⁺ binds 4.8 EC carbonyl O.
- **Analysis:** over the last 4 ns, `ucmd-analyze shell` at the first g(r) minimum and at
  0.516 nm (EC:O:1, EMC:O:1, PF6:P), `residence`, `clusters`.
- **Reading:** if EC rises well above 21 % (towards or above its 50 % share), the carbonyl
  charge model is the lever, as the strategy assumes. If not, the cause lies elsewhere (LJ of
  the carbonyl O, EMC's own parameters, or ζ's effect on Li⁺–O binding).
- **Caveat:** one ion gives one shell at a time; with EMC residence times of about 0.6 ns, 4 ns
  hold only a handful of independent shells. The difference between M0 and M1 must be large to
  count.

## Result, 2026-11-21

Run finished 2026-11-20 22:34Z on HIP: 58 min wall, no hang, ⟨ρ⟩ 1.1664 g/cm³ (M0: 1.1499).
Li⁺ stayed free of PF₆⁻ throughout. Last 4 ns, 2000 frames:

| | M0 (A4) | **M1** |
|---|---|---|
| first shell (r < 0.28 nm), EC O=C / EMC O=C | 0.86 / 3.63 | **1.41 / 3.19** |
| EC share of the first-shell carbonyl O | 19 ± 4 % | **31 ± 7 %** |
| per ns (1–2, 2–3, 3–4, 4–5) | 19, 24, 24, 8 % | 48, 35, 17, 22 % |
| within 0.516 nm (Lehnert's rs), EC / EMC | 1.63 / 3.97 (29 %) | 2.20 / 3.44 (39 %) |
| continuous residence at Li⁺ (0.30 nm), EC / EMC | 24 / 250 ps | 42 / 303 ps |
| intermittent residence, EC / EMC | 118 / ~2000 ps | 272 / 2043 ps |
| distinct molecules in contact, EC / EMC | 25 / 15 | 36 / 14 |

Errors are the SEM over 4 × 1 ns blocks. The blocks are correlated (EMC stays about 2 ns,
intermittent), so the true uncertainty is larger.

**Reading:**
1. M1 moves EC towards its share (19 → 31 %) and nearly doubles its residence time. This is the
   direction the gas-phase test predicts (M1 recovers a third of the QM EC–DMC difference).
2. The shift is 1.4 standard errors, from one ion. It is a trend, not a result.
3. EC stays below its 50 % share and below Lehnert's ≈ 47 % at rs (Fig. S10). The carbonyl
   charges are part of the answer, not all of it, as layer 0 suggested.
4. M1 took EC from 31 % in its first nanosecond to about 20 % later. A single ion cannot tell
   whether this is drift or one long EMC visit.

Commands (ucmd-analysis venv; M0 the same on the A4 trajectory):

```sh
ucmd-analyze shell TRAJ.h5 --skip-ps 1000 --a Li:Li --b EC:O:1 --b EMC:O:1 --b PF6:P \
    --r-cut-nm 0.28 --r-cut-nm 0.28 --r-cut-nm 0.28   # corrected 2026-11-21: without it, auto per pair
ucmd-analyze shell TRAJ.h5 --skip-ps 1000 --a Li:Li --b EC:O:1 --b EMC:O:1 --b PF6:P \
    --r-cut-nm 0.516 --r-cut-nm 0.516 --r-cut-nm 0.516
ucmd-analyze residence TRAJ.h5 --a Li:Li --b EC:O:1 --r-cut-nm 0.30   # and EMC:O:1
ucmd-analyze clusters TRAJ.h5 --cation Li:Li --anion PF6:P
```

The per-nanosecond split counts carbonyl O within 0.28 nm of Li⁺ (minimum image) frame by frame.
