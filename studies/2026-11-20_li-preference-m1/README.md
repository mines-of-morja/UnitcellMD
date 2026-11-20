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
- **Comparison (M0):** the 1:1 run of the A4 study. First 2.07 ns analysed on 2026-11-20 (raw
  trajectory: shell counts around the single Li⁺ do not depend on the labels of identical
  solvent molecules): first shell EC O=C 0.92, EMC O=C 3.52 (EC 21 %); within 0.516 nm (Lehnert's
  rs) EC 1.84, EMC 3.78 (EC 33 %). In pure EC the same Li⁺ binds 4.9 EC carbonyl O.
- **Analysis:** over the last 4 ns, `ucmd-analyze shell` at the first g(r) minimum and at
  0.516 nm (EC:O:1, EMC:O:1, PF6:P), `residence`, `clusters`.
- **Reading:** if EC rises well above 21 % (towards or above its 50 % share), the carbonyl
  charge model is the lever, as the strategy assumes. If not, the cause lies elsewhere (LJ of
  the carbonyl O, EMC's own parameters, or ζ's effect on Li⁺–O binding).
- **Caveat:** one ion gives one shell at a time; with EMC residence times of about 0.6 ns, 4 ns
  hold only a handful of independent shells. The difference between M0 and M1 must be large to
  count.
