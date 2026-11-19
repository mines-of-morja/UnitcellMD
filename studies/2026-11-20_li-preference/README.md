# Li⁺ preference without salt crowding (calculation plan A4), prepared 2026-11-19

- **Question:** in the 1 M electrolyte the Li⁺ shell holds 3.7 EMC and 0.4 EC carbonyl O
  (report §3.4), although EC is 34 % of the solvent molecules. Is this a property of the current
  parameters (EC's carbonyl O at −0.393 e vs EMC's −0.531 e), or a crowding effect of the salt?
- **Systems:** one LiPF₆ pair in 500 EC, in 500 EMC, and in 250 EC + 250 EMC (1:1 by
  molecules).
  - Pure EC at 20 °C is supercooled (EC melts at 36 °C), as it is in the electrolyte.
  - ζ = 0.75 as in the electrolyte.
- **Protocol:** the electrolyte study's settings (1 fs, Nosé–Hoover τ = 0.1 ps, C-rescale /
  Monte Carlo barostat at 1 atm, 1.4 nm, PME 1e-5, tail correction on), 5 ns NPT on the GPU,
  mixed precision. A frame every 2 ps for residence times.
- **Analysis:** over the last 4 ns, run `ucmd-analyze shell` (carbonyl O of EC and EMC, P of
  PF₆⁻), `residence` and `clusters`. Then compare the EC share of the shell in the 1:1 mixture
  with its 50 % share of the molecules.
- **Caveats:**
  - One ion gives one shell at a time. 4 ns holds only as many independent shells as there
    are exchanges (see the residence times).
  - The pair may stay in contact, in which case the solvent shell is that of the pair, not of a
    free Li⁺. The cluster output tells which.
- **Status:** planned, not started. It runs on the GPU after the transport pilot (about 7 h
  for the three runs).
