# Trial T2: EC model at 1 M (M0 or M1), prepared 2026-11-21

- **Plan and decision rule:** [docs/research/trials/T2-ec-model-1M.md](../../docs/research/trials/T2-ec-model-1M.md),
  committed before the runs (a114257).
- **Systems:** six, `recipes/t2_{m0,m1}_s{1,2,3}.toml`: Lehnert's 1 M box (47 LiPF₆ at ζ = 0.75,
  168 EC, 332 EMC, 7036 atoms), start edge 4.27 nm, packing seeds 20261124–26. M1 differs from M0
  only in the EC parameters (Caleman 2012, local explicit copy from `2026-11-20_ec-opls-test`).
- **Protocol:** the replica study's, unchanged: NPT 1 atm, 20 °C, 5 ns, HIP mixed precision; last
  4 ns analysed.
- **Cost:** 6 runs of about 1.1 h on HIP, GPU queue 8 (2026-11-21 night).
